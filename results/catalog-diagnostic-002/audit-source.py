"""Privileged post-run diagnostic. NEVER imported by a controller.

Answer-set oracle over recorded catalogs is not semantic proof, trained policy,
or a certified budget-feasible recovery rate. Query timeouts remain unknown.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from flagship_controller.structured_runtime import StructuredGraph
from flagship_controller.webqsp_runtime import Blocked, NS
from flagship_controller.official_score import prf


def linked_anchors(record):
    anchors=[]
    for event in record['trace']:
        if event['action']=='LINK':
            if len(event['candidates'])==1:anchors.append(event['candidates'][0])
        elif event['action']=='DISAMBIGUATE':
            if event['choice'].get('supported'):anchors.append(event['choice']['entity'])
    return anchors


def gold_query(sparql):
    text=re.sub(r'(?im)^\s*PREFIX\s+ns:\s*<http://rdf.freebase.com/ns/>\s*','',sparql).strip()
    if not re.match(r'(?is)^SELECT\s+(?:DISTINCT\s+)?\?x\b',text):raise ValueError('Unsupported official SELECT form')
    if re.search(r'\b(SERVICE|FROM|INSERT|DELETE|LOAD|CLEAR|DROP)\b',text,re.I):raise ValueError('Nonlocal query rejected')
    return 'SELECT DISTINCT ?answer WHERE { { '+text+' } BIND(?x AS ?answer) } LIMIT 101'


def audit(records,annotations,graph,on_result=None):
    labels={r['id']:r for r in annotations};rows=[]
    for record in records:
        label=labels[record['id']];parses=label['parses']
        eligible=any(p.get('AnnotatorComment',{}).get('QuestionQuality')=='Good' and p.get('AnnotatorComment',{}).get('ParseQuality')=='Complete' for p in parses)
        row={'id':record['id'],'scorable':eligible,'catalog_candidates':0,'candidate_results':[], 'official_query_results':[]}
        if not eligible:
            rows.append(row);continue
        anchors=linked_anchors(record)
        catalog=next((t['programs'] for t in record['trace'] if t['action']=='PROGRAM_CATALOG'),[])
        row['catalog_candidates']=len(catalog)
        row['linked_topic_matches_any_annotation']=bool(anchors) and any(anchors[0]==p.get('TopicEntityMid') for p in parses)
        chains=[p.get('InferentialChain') or [] for p in parses]
        inventory=next((t['inventory'] for t in record['trace'] if t['action']=='INVENTORY'),[])
        available=next((t['available'] for t in record['trace'] if t['action']=='INVENTORY'),[])
        roots=next((t['roots'] for t in record['trace'] if t['action']=='SCHEMA'),[])
        for name,relations in [('inventory',inventory),('ranked_roots',available),('chosen_roots',roots)]:
            row['any_annotated_first_relation_in_'+name]=any(c and c[0] in {r['relation'] for r in relations} for c in chains)
        score=lambda answers:max(prf([a['AnswerArgument'] for a in p['Answers']],answers)[2] for p in parses)
        for candidate in catalog:
            outcome={'index':candidate['index'],'program':candidate['program']}
            try:
                answers,_=graph.execute(anchors,candidate['program'])
                outcome.update(status='complete',answer_count=len(answers),best_f1=score(answers))
            except (Blocked,OSError,ValueError,KeyError) as error:
                outcome.update(status='unknown',reason=type(error).__name__+':'+str(error))
            row['candidate_results'].append(outcome)
        known=[c['best_f1'] for c in row['candidate_results'] if c['status']=='complete']
        row['known_catalog_best_f1']=max(known) if known else None
        row['catalog_answer_set_exact_found']=any(f==1. for f in known)
        row['catalog_completely_evaluated']=bool(catalog) and len(known)==len(catalog)
        for parse in parses:
            entry={'parse_id':parse.get('ParseId'),'source_query_sha256':hashlib.sha256(parse['Sparql'].encode()).hexdigest()}
            try:
                found=graph.select(gold_query(parse['Sparql']))
                answers=[r['answer']['value'].removeprefix(NS) for r in found]
                entry.update(status='complete',answer_count=len(answers),f1_to_this_parse=prf([a['AnswerArgument'] for a in parse['Answers']],answers)[2])
            except (Blocked,OSError,ValueError,KeyError) as error:entry.update(status='unknown',reason=type(error).__name__+':'+str(error))
            row['official_query_results'].append(entry)
        rows.append(row)
        if on_result:on_result(row)
    return {'scope':'Post-run annotated-training diagnostic, answer-set catalog oracle and official-query availability; not runtime, semantic certification, or final-test performance',
            'snapshot':graph.snapshot,'query_timeout_seconds':graph.timeout,'rows':rows,
            'n_questions':len(rows),'catalog_exact_found':sum(r.get('catalog_answer_set_exact_found',False) for r in rows),
            'catalog_completely_evaluated':sum(r.get('catalog_completely_evaluated',False) for r in rows),
            'query_calls':graph.calls,'query_audit':graph.audit,
            'limitation':'Query availability can reveal mismatch but does not establish snapshot identity. Best-F1 candidate may be semantically accidental. Off-policy graph costs are not inference costs or feasible-continuation labels.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('study',type=Path);parser.add_argument('labels',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--endpoint',default='http://127.0.0.1:8891/sparql');args=parser.parse_args()
    if args.output.exists():parser.error('Refuse overwrite')
    plan=json.loads((args.study/'plan.json').read_text())
    records=[r for r in map(json.loads,(args.study/'predictions.jsonl').read_text().splitlines()) if r['variant']=='fixed']
    labels=[r for r in map(json.loads,args.labels.read_text().splitlines()) if r['id'] in plan['question_ids']]
    graph=StructuredGraph(args.endpoint,plan['snapshot'],max_calls=300,timeout=5)
    result=audit(records,labels,graph,on_result=lambda r:print(r['id'],'catalog',r['known_catalog_best_f1'],'all',r['catalog_completely_evaluated'],flush=True))
    result['source_predictions_sha256']=hashlib.sha256((args.study/'predictions.jsonl').read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with open(args.output,'x',opener=lambda p,f:__import__('os').open(p,f,0o600)) as output:output.write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
