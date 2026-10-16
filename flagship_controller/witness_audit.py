"""Independent offline consistency audit of recorded conjunctive-query witnesses.

Does not import the deployed compiler/checker or read answer labels. This checks
recorded proof/row consistency, not question meaning or graph completeness.
"""
import argparse
import json
from pathlib import Path

NS='http://rdf.freebase.com/ns/'


def audit(record):
    if record['terminal']!='ANSWER':
        if record['answers']:raise ValueError('Abstention contains answers')
        return {'id':record['id'],'answered':False,'witnesses':0,'semantic_validity':'not assessed'}
    plans=[t['program'] for t in record['trace'] if t['action'] in ('PLAN','REPAIR_PLAN')]
    if not plans:raise ValueError('No recorded plan')
    program=plans[-1];anchors=[]
    for t in record['trace']:
        if t['action']=='LINK':
            if len(t['candidates'])==1:anchors.append(t['candidates'][0])
        elif t['action']=='DISAMBIGUATE':
            selected=t['choice']['entity']
            if t['choice'].get('supported') is not True or selected not in [c['entity'] for c in t['cards']]:raise ValueError('Unobserved selected anchor')
            anchors.append(selected)
    if not anchors:raise ValueError('No recorded anchors')
    if len(set(record['answers']))!=len(record['answers']):raise ValueError('Duplicate emitted answers')
    if {c['anchor'] for c in program['constraints']}!=set(range(1,len(anchors))):raise ValueError('Unbound secondary anchor')
    expected=[]
    for i,step in enumerate(program['steps']):
        if step['direction'] not in ('in','out'):raise ValueError('Invalid direction')
        a,b=('v'+str(i),'v'+str(i+1))
        expected.append((a,step['relation'],b) if step['direction']=='out' else (b,step['relation'],a))
    for c in program['constraints']:
        a,b='v'+str(c['at']),'anchor'+str(c['anchor'])
        expected.append((a,c['relation'],b) if c['direction']=='out' else (b,c['relation'],a))
    if not record['witnesses']:raise ValueError('Answer has no witness')
    answers=set();query_indices=set()
    for witness in record['witnesses']:
        if len(witness)!=len(expected):raise ValueError('Incomplete witness')
        bindings={'v0':{'type':'uri','value':NS+anchors[0]}}
        bindings.update({'anchor'+str(i):{'type':'uri','value':NS+a} for i,a in enumerate(anchors)})
        for edge,(source,relation,target) in zip(witness,expected):
            if edge['relation']!=relation:raise ValueError('Predicate mismatch')
            for variable,term in [(source,edge['source']),(target,edge['target'])]:
                if variable in bindings and bindings[variable]!=term:raise ValueError('Inconsistent endpoint or anchor')
                bindings[variable]=term
            provenance=edge['provenance'];index=provenance['query_index']
            if type(index) is not int or not 0<=index<len(record['graph_audit']):raise ValueError('Missing recorded query')
            query=record['graph_audit'][index]
            if provenance['snapshot']!=query['snapshot']:raise ValueError('Snapshot mismatch')
            if query.get('sql_state') is not None and query['sql_state'].strip()!='00000':raise ValueError('Incomplete query state')
            query_indices.add(index)
        for index in {e['provenance']['query_index'] for e in witness}:
            if not any(all(row.get('v'+str(i))==bindings['v'+str(i)] for i in range(1,len(program['steps'])+1)) for row in record['graph_audit'][index]['rows']):
                raise ValueError('Witness has no matching recorded result row')
        term=bindings['v'+str(len(program['steps']))]
        answers.add(term['value'][len(NS):] if term['type']=='uri' and term['value'].startswith(NS) else term['value'])
    if answers!=set(record['answers']):raise ValueError('Emitted answers differ from witnessed endpoints')
    if len(query_indices)!=1:raise ValueError('Expected one complete conjunctive result query')
    rows=record['graph_audit'][next(iter(query_indices))]['rows']
    if len(rows)!=len(record['witnesses']):raise ValueError('Dropped or duplicated witness rows')
    return {'id':record['id'],'answered':True,'witnesses':len(record['witnesses']),'answers':len(answers),
            'recorded_row_consistency':True,'semantic_validity':'not assessed'}


def main():
    p=argparse.ArgumentParser();p.add_argument('predictions',type=Path);a=p.parse_args()
    reports=[]
    for line in a.predictions.read_text().splitlines():
        if line.strip():reports.append(audit(json.loads(line)))
    print(json.dumps({'scope':'independent recorded-row/constraint witness consistency, not semantic accuracy',
                      'answered':sum(r['answered'] for r in reports),'rows':reports},indent=2))
if __name__=='__main__':main()
