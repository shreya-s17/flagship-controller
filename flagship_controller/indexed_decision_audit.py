"""Offline ledger audit of indexed choices and verbatim native spans.

Checks provenance/representation, not meaning, truth or completeness of answers.
Invalid model choices may be retained as abstentions; they must never emit IDs.
"""
import argparse
import json
import math
from pathlib import Path


def audit(record):
    native=record.get('native_response') or '';presented=None;beam=[]
    checks=[];invalid=0;projected=[]
    for event in record['trace']:
        action=event['action']
        if action=='RELATION_PRESENTATION':presented=event['presented']
        if action=='ENTITY_PRUNE' and event['ids']:beam=event['ids']
        if action not in ('INDEXED_RELATION_SELECTION','NATIVE_SPAN_EXTRACTION'):continue
        if event.get('model_call_skipped'):
            checks.append({'action':action,'model_request_skipped':True});continue
        index=event['cost']['model_calls']-1
        if not 0<=index<len(record['model_audit']):raise ValueError('Selection has no returned model request')
        call=record['model_audit'][index]
        if json.loads(call['response'])!=event['selection']:raise ValueError('Selection differs from raw returned response')
        inputs=call['prompt']['inputs'];selection=event['selection'];valid=isinstance(selection,dict)
        if action=='INDEXED_RELATION_SELECTION':
            names=event['candidates']
            if presented is None or set(names)!=set(presented):raise ValueError('Relation presentation differs')
            if inputs['relations']!=[{'index':i,'relation':name} for i,name in enumerate(names)]:
                raise ValueError('Presented relations differ from actual model input')
            choices=selection.get('selections') if valid else None
            valid=isinstance(choices,list) and len(choices)<=3
            seen=set()
            for choice in choices if isinstance(choices,list) else []:
                if not isinstance(choice,dict):valid=False;continue
                i=choice.get('index');score=choice.get('score')
                if type(i) is not int or not 0<=i<len(names) or i in seen:valid=False
                else:seen.add(i)
                if type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=1:valid=False
        else:
            spans=event['spans'];candidates=event['candidates']
            if inputs['native_response']!=native or inputs['spans']!=spans:raise ValueError('Native extraction input differs')
            if any(c['entity'] not in beam for c in candidates):raise ValueError('Candidate outside final observed beam')
            allowed={c['entity'] for c in candidates}
            for span in spans:
                a,b=span['start'],span['end']
                if type(a) is not int or type(b) is not int or not 0<=a<b<=len(native) or native[a:b]!=span['quote']:
                    raise ValueError('Quote is not an actual source span')
                if span['entity'] not in allowed:raise ValueError('Span candidate unobserved')
            choices=selection.get('span_indices') if valid else None
            valid=isinstance(choices,list);seen=set()
            for i in choices if isinstance(choices,list) else []:
                if type(i) is not int or not 0<=i<len(spans) or i in seen:valid=False
                else:seen.add(i)
            if valid and selection.get('supported') is True and selection.get('all_concluded_answers_represented') is True:
                projected=list(dict.fromkeys(spans[i]['entity'] for i in choices))
        if not valid:invalid+=1
        checks.append({'action':action,'returned_request_index':index,'decoder_output_valid':valid})
    if invalid and record['terminal']!='ABSTAIN':raise ValueError('Invalid decoder output emitted an answer')
    if record['terminal']=='ANSWER' and (not projected or set(projected)!=set(record['answers'])):
        raise ValueError('Answer differs from explicit native-span projection')
    if record['terminal']=='ABSTAIN' and record['answers']:raise ValueError('Abstention emitted IDs')
    if record['cost']['model_usage_complete']!=(record['cost']['model_calls']==len(record['model_audit'])):
        raise ValueError('Usage completeness flag differs from ledger')
    return {'id':record['id'],'terminal':record['terminal'],'reason':record['reason'],
        'checks':checks,'invalid_decoder_outputs_retained':invalid,
        'semantic_validity':'not assessed; model conclusion/completeness flags are not independent labels'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('predictions',type=Path);args=parser.parse_args()
    rows=[json.loads(line) for line in args.predictions.read_text().splitlines() if line.strip()]
    print(json.dumps({'scope':'Offline representation/request-ledger checks, not semantic certification',
        'records':[audit(row) for row in rows if row['variant']=='tog-indexed-spans']},indent=2))
