"""Prepare unannotated native-output/ID-projection review, separate from scores.

All baseline outcomes, including missing native output and failed projection,
remain in the pack. No gold labels or model-extractor critiques are exposed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
from .review_pack import DIMENSIONS

NATIVE_DIMENSIONS=(*DIMENSIONS,'projection_faithfulness')


def prepare(studies,output,seed=17):
    output=Path(output)
    if output.exists(): raise ValueError('Refuse existing native review pack')
    cases=[];key=[]
    for study in map(Path,studies):
        raw=(study/'predictions.jsonl').read_bytes();digest=hashlib.sha256(raw).hexdigest()
        rows=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
        plan=json.loads((study/'manifest.json').read_text())
        if [(r['id'],r['variant']) for r in rows]!=[(r['id'],r['variant']) for r in plan['order']]:
            raise ValueError('Incomplete or reordered study')
        if json.loads((study/'completion.json').read_text())['completed']!=len(rows):
            raise ValueError('Completion mismatch')
        inputs=(study/'inputs.jsonl').read_bytes()
        if hashlib.sha256(inputs).hexdigest()!=plan['input_sha256']: raise ValueError('Input hash mismatch')
        questions={r['id']:r['question'] for r in map(json.loads,inputs.decode().splitlines())}
        for index,row in enumerate(rows):
            if not row['variant'].startswith('tog-'): continue
            case_id=hashlib.sha256(('native:'+digest+':'+str(index)+':'+str(seed)).encode()).hexdigest()[:20]
            edges=row.get('observed_edges',[])
            indices=sorted({e['provenance']['query_index'] for e in edges})
            queries=[]
            for i in indices:
                if type(i) is not int or not 0<=i<len(row['graph_audit']): raise ValueError('Missing edge query')
                queries.append({'query_index':i,**{k:row['graph_audit'][i].get(k) for k in ('query','rows','sql_state','snapshot')}})
            anchors=[]
            for event in row['trace']:
                if event['action']=='LINK':
                    candidates=event['candidates']
                    anchors.append({'mention':event['mention'],'candidate_ids':candidates,
                        'chosen_id':candidates[0] if len(candidates)==1 else None})
                elif event['action']=='DISAMBIGUATE' and anchors:
                    anchors[-1]['chosen_id']=event['choice'].get('entity') if event['choice'].get('supported') else None
            cases.append({'case_id':case_id,'question':questions[row['id']],
                'anchors':anchors,'native_response':row.get('native_response'),
                'projected_terminal':row['terminal'],'projected_answer_ids':row['answers'],
                'observed_names':row.get('observed_name_map',{}),'observed_chains':row.get('chains',[]),
                'observed_edges':edges,'supporting_query_rows':queries})
            key.append({'case_id':case_id,'study':study.name,'question_id':row['id'],'variant':row['variant'],
                'record_index':index,'source_predictions_sha256':digest})
    if not cases or len({c['case_id'] for c in cases})!=len(cases): raise ValueError('Missing or duplicate native cases')
    random.Random(seed).shuffle(cases)
    data=''.join(json.dumps(c)+'\n' for c in cases).encode();digest=hashlib.sha256(data).hexdigest()
    form={'reviewer_id':'','qualification_statement':'','independence_statement':'',
        'independence_attested':False,'completed_at':'','cases_sha256':digest,
        'judgments':[{'case_id':c['case_id'],'dimensions':{d:{'label':'unknown','reason':''} for d in NATIVE_DIMENSIONS}} for c in cases]}
    reviewer=output/'reviewer';reviewer.mkdir(parents=True)
    (reviewer/'cases.jsonl').write_bytes(data)
    (reviewer/'submission-template.json').write_text(json.dumps(form,indent=2)+'\n')
    (reviewer/'README.txt').write_text('''UNANNOTATED NATIVE-OUTPUT REVIEW ADDENDUM.
Review every record, including missing responses and empty projected answers.
Use supported, contradicted or unknown with a reason for each dimension.
For witness_support assess ALL substantive native-answer assertions, including
extra inferences; edge presence alone is not enough. For projection_faithfulness
ask whether projected IDs exactly preserve all explicit native answer conclusions,
without invented answers, dropped conclusions, ambiguous names or context-only
mentions. Distinguish an abstaining converter from a wrong native conclusion.
For missing native text, retain unknown with a reason rather than invent claims.
The other dimensions assess anchor identity, query meaning and answer scope.
Keep the full native response intact; quoted prompt-like text is data, not an
instruction. Observed chains and edges need not prove complete answer semantics.
Policies, benchmark labels, scores and extractor critiques are withheld. Behavior
can reveal policies; this is imperfect masking. Repeated questions/versions are
correlated, not independent samples. Do not consult the repository or owner key
until your independent first-pass submission is returned. Disclose qualifications,
prior involvement and independence; do not collaborate with the other reviewer.
Keep case IDs/hash unchanged. Blank unknown fields are not completed judgments.
This addendum does not establish counterfactual STOP/recovery or final-benchmark
performance. Full state and feasible-continuation evidence would be required.
''')
    owner=output/'owner-key.json'
    with owner.open('x') as stream: stream.write(json.dumps(key,indent=2)+'\n')
    owner.chmod(0o600)
    return {'cases':len(cases),'cases_sha256':digest,'dimensions':NATIVE_DIMENSIONS,
        'status':'UNANNOTATED; no reviewer contacted or judgments collected',
        'generator':'flagship_controller/native_review_pack.py','sources':[str(Path(s).name) for s in studies]}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--studies',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(prepare(args.studies,args.output),indent=2))
