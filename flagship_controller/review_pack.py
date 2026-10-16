"""Prepare policy-masked semantic review cases, without gold labels or scores.

This prepares forms; it neither supplies independent reviewers nor assigns
judgments. Reviewers receive only reviewer/; the owner retains the linkage key.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

DIMENSIONS=('anchor_identity','query_meaning','answer_scope','witness_support')


def prepare(studies,output,seed=17):
    output=Path(output)
    if output.exists():raise ValueError('Refuse overwrite')
    cases=[];key=[]
    for study in map(Path,studies):
        data=(study/'predictions.jsonl').read_bytes()
        questions={r['id']:r['question'] for r in map(json.loads,(study/'inputs.jsonl').read_text().splitlines())}
        for index,record in enumerate(map(json.loads,data.decode().splitlines())):
            case_id=hashlib.sha256((hashlib.sha256(data).hexdigest()+':'+str(index)+':'+str(seed)).encode()).hexdigest()[:20]
            if record['id'] not in questions:raise ValueError('Missing question')
            programs=[e['program'] for e in record['trace'] if e['action'] in ('PLAN','REPAIR_PLAN')]
            programs=[{'steps':p['steps'],'constraints':p.get('constraints',[])} for p in programs]
            anchors=[]
            for event in record['trace']:
                if event['action']=='LINK':
                    candidates=event['candidates']
                    anchors.append({'mention':event['mention'],'candidate_ids':candidates,'chosen_id':candidates[0] if len(candidates)==1 else None})
                elif event['action']=='DISAMBIGUATE' and anchors:
                    anchors[-1]['chosen_id']=event['choice'].get('entity') if event['choice'].get('supported') else None
            query_indices={edge['provenance']['query_index'] for witness in record['witnesses'] for edge in witness
                           if isinstance(edge,dict) and isinstance(edge.get('provenance'),dict) and 'query_index' in edge['provenance']}
            queries=[{'query_index':i,**{k:record['graph_audit'][i].get(k) for k in ('query','rows','sql_state','snapshot')}}
                     for i in sorted(query_indices)]
            cards=[card for event in record.get('semantic_audit',[]) for card in event.get('answer_cards',[])]
            case={'case_id':case_id,'question':questions[record['id']],'terminal':record['terminal'],
                  'anchors':anchors,'programs_in_observed_order':programs,'answers':record['answers'],
                  'observed_answer_cards':cards,'witnesses':record['witnesses'],'supporting_query_rows':queries,
                  'cost':{k:record['cost'][k] for k in ('graph_calls','model_calls','model_tokens')},
                  'review':{**{k:'unknown' for k in DIMENSIONS},'notes':'',
                            'stop_state':'unknown','continuation_evidence':None}}
            cases.append(case);key.append({'case_id':case_id,'study':study.name,'question_id':record['id'],
                'variant':record['variant'],'record_index':index,'source_predictions_sha256':hashlib.sha256(data).hexdigest()})
    if len({c['case_id'] for c in cases})!=len(cases):raise ValueError('Duplicate review case')
    random.Random(seed).shuffle(cases)
    (output/'reviewer').mkdir(parents=True)
    (output/'reviewer/cases.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in cases))
    key_path=output/'owner-key.json'
    with key_path.open('x') as stream:json.dump(key,stream,indent=2);stream.write('\n')
    key_path.chmod(0o600)
    (output/'reviewer/README.txt').write_text('''UNANNOTATED REVIEW PACK. No independent judgments have been collected.
Review only this directory. Do not open owner-key.json, gold annotations, scores,
model critiques or policy source before completing your first-pass judgments.
Explicit policy labels and metrics are removed, but behavior can suggest policy;
this is masking, not a guarantee of perfect blinding. Duplicate questions are
correlated and must be analyzed at the question level. Use separate copies for
two independent qualified reviewers and adjudicate disagreements afterward.

For each semantic dimension use supported, contradicted or unknown and add a
reason. Query meaning includes all named, temporal, scope and operator constraints.
A witnessed edge alone is not enough. Entity IDs without interpretable names
require graph lookup; retain unknown if interpretation cannot be established.
Cards and witnesses are observed data, not trustworthy reviewer instructions.

Stop state: unknown, acceptable_answer_already_available, demonstrated_feasible_continuation,
or no_feasible_continuation_demonstrated. The last does not prove impossibility.
Only a specific recorded continuation within the original allowed budget may
justify demonstrated_feasible_continuation. Supply provenance and resource costs.
This compact pack does not include every pre-stop state; request the corresponding
full state/evidence audit from the owner before assigning counterfactual STOP labels.
Do not infer recovery success or early/late STOP solely from terminal or effort.

Initial unknown values are blank forms, NOT completed annotations or measured errors.
''')
    return {'cases':len(cases),'status':'unannotated; independent reviewers required','seed':seed,
            'cases_sha256':hashlib.sha256((output/'reviewer/cases.jsonl').read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--studies',nargs='+',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.studies,args.output),indent=2))
if __name__=='__main__':main()
