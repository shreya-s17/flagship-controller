"""After an experiment, independently requery every unique accepted witness triple.

No model or gold labels are used. Run AFTER timing measurements, so auditing
cannot warm their graph cache. This confirms triples, not question semantics.
"""
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.webqsp_runtime import Freebase, NS, identifier, Blocked
from flagship_controller.witness_audit import audit


def sparql_term(term):
    if term['type']=='uri':
        if not term['value'].startswith(NS):raise ValueError('Only Freebase entity IRIs supported')
        return identifier(term['value'][len(NS):])
    if term['type'] not in ('literal','typed-literal'):raise ValueError('Unsupported RDF term')
    literal=json.dumps(term['value'])
    if term.get('xml:lang'):
        lang=term['xml:lang']
        if not re.fullmatch(r'[A-Za-z]+(?:-[A-Za-z0-9]+)*',lang):raise ValueError('Invalid language tag')
        literal+='@'+lang
    elif term.get('datatype'):
        datatype=term['datatype']
        if not re.fullmatch(r'https?://[A-Za-z0-9._:/#-]+',datatype):raise ValueError('Invalid datatype IRI')
        literal+='^^<'+datatype+'>'
    return literal


def recheck(records,graph):
    triples={}
    for record in records:
        audit(record)
        if record['terminal']!='ANSWER':continue
        for witness in record['witnesses']:
            for edge in witness:
                if edge['provenance']['snapshot']!=graph.snapshot:raise ValueError('Snapshot mismatch')
                triple=sparql_term(edge['source'])+' '+identifier(edge['relation'])+' '+sparql_term(edge['target'])
                triples[triple]=True
    if len(triples)>2000:raise ValueError('Audit triple cap')
    rows=[]
    for triple in sorted(triples):
        try:
            observed=graph.select('SELECT (1 AS ?ok) WHERE { '+triple+' . } LIMIT 1')
            rows.append({'triple':triple,'status':'present' if observed else 'not_observed'})
        except (Blocked,OSError,ValueError,KeyError) as error:
            rows.append({'triple':triple,'status':'unknown','reason':type(error).__name__+':'+str(error)})
    return {'scope':'post-run independent constant-triple graph requery; not semantic entailment or truth calibration',
        'snapshot':graph.snapshot,'unique_triples':len(triples),'present':sum(r['status']=='present' for r in rows),
        'not_observed':sum(r['status']=='not_observed' for r in rows),'unknown':sum(r['status']=='unknown' for r in rows),
        'queries':graph.audit,'rows':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('predictions',type=Path);p.add_argument('--endpoint',required=True);p.add_argument('--snapshot',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Refuse to overwrite audit output')
    records=[json.loads(x) for x in a.predictions.read_text().splitlines() if x.strip()]
    result=recheck(records,Freebase(a.endpoint,a.snapshot,max_calls=2000))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('queries','rows')},indent=2))
