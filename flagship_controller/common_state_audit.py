"""Independent offline state/usage/declaration ledger checks, never semantics."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def committed(path):
    envelope=json.loads(path.read_text())
    if digest(envelope['value'])!=envelope['sha256']:raise ValueError('Journal content mismatch')
    return envelope


def check(folder):
    folder=Path(folder);plan=json.loads((folder/'manifest.json').read_text())
    raw=(folder/'predictions.jsonl').read_bytes();rows=list(map(json.loads,raw.decode().splitlines()))
    completion=json.loads((folder/'completion.json').read_text())
    if completion['completed']!=len(rows) or completion['predictions_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('Completion mismatch')
    if [(r['id'],r['seed'],r['variant']) for r in rows]!=[(r['id'],r['seed'],r['variant']) for r in plan['order']]:raise ValueError('Frozen order mismatch')
    checked=[];packets={}
    for index,row in enumerate(rows):
        key=str(row['seed'])+'-'+hashlib.sha256(row['id'].encode()).hexdigest()[:16]
        envelope=committed(folder/'journal'/(key+'-prefix.json'));packet=envelope['value'];packets[key]=packet
        result=committed(folder/'journal'/f'policy-{index:04d}.json')
        if result['item']!={**plan['order'][index],'prefix_sha256':digest(packet)}:raise ValueError('Policy/prefix link mismatch')
        if any(row.get(k)!=v for k,v in result['value'].items()):raise ValueError('Prediction differs from committed policy outcome')
        baseline=row['variant'].startswith('tog-');prefix=packet['link'] if baseline else packet['internal']
        if row['cost'].get('cost_is_lower_bound'):
            if row['terminal']!='ABSTAIN' or row['answers'] or row['cost']['model_usage_complete']:
                raise ValueError('Interrupted output not marked conservatively')
            checked.append({'id':row['id'],'seed':row['seed'],'variant':row['variant'],'status':'retained interrupted/unknown-cost abstention'});continue
        if not row.get('policy_continuation_executed'):
            if row['terminal']!='ABSTAIN' or row['answers'] or row['reason']!=packet['capture_result']['reason']:
                raise ValueError('Common failure changed across policy')
            checked.append({'id':row['id'],'seed':row['seed'],'variant':row['variant'],'status':'common pre-policy failure retained'});continue
        n=len(prefix['provider_audit']);g=len(prefix['graph_audit'])
        if row['shared_state']['replayed_model_calls']!=n or row['shared_state']['replayed_graph_calls']!=g:
            raise ValueError('Replay count mismatch')
        for saved,replayed in zip(prefix['provider_audit'],row['provider_audit'][:n]):
            if saved['payload_sha256']!=replayed['payload_sha256'] or saved['response']!=replayed['response'] or not replayed['replayed']:
                raise ValueError('Provider prefix differs')
        for saved,replayed in zip(prefix['graph_audit'],row['graph_audit'][:g]):
            if any(saved.get(k)!=replayed.get(k) for k in ('query','rows','snapshot','sql_state')) or not replayed['replayed_prefix']:
                raise ValueError('Graph prefix differs')
        for request in row['provider_audit']:
            if request['seed']!=row['seed'] or request['payload']['options']['seed']!=row['seed'] or digest(request['payload'])!=request['payload_sha256']:
                raise ValueError('Actual request seed/hash mismatch')
        if row['cost']['physical_new_model_calls']!=sum(not e['replayed'] for e in row['provider_audit']):raise ValueError('Physical model count mismatch')
        if row['cost']['physical_new_graph_calls']!=row['cost']['graph_calls']-g:raise ValueError('Physical graph count mismatch')
        if row['cost']['model_tokens']!=sum(e['input_tokens']+e['output_tokens'] for e in row['model_audit']):raise ValueError('Known token accounting mismatch')
        if row['cost']['model_usage_complete']!=(row['cost']['model_calls']==len(row['model_audit'])):raise ValueError('Usage completeness mismatch')
        if not baseline:
            for action,keyname in [('PROGRAM_CATALOG','programs'),('PLAN','program')]:
                expected=next(e[keyname] for e in packet['capture_result']['trace'] if e['action']==action)
                observed=next(e[keyname] for e in row['trace'] if e['action']==action)
                if expected!=observed:raise ValueError('Internal catalog/first choice differs')
        elif row['terminal']=='ANSWER':
            event=next(e for e in reversed(row['trace']) if e['action']=='DECLARED_JSON_REASONING')
            response=json.loads(row['native_response'])
            if response!=event['response'] or response['decision']!='ANSWER':raise ValueError('Native declaration differs')
            candidates=event['candidates'];indices=response['answer_indices']
            if not indices or len(set(indices))!=len(indices) or any(type(i) is not int or not 0<=i<len(candidates) for i in indices):raise ValueError('Invalid declared indices')
            if any(c['names']!=row['observed_name_map'].get(c['entity']) for c in candidates):raise ValueError('Declared candidate name unobserved')
            if set(row['answers'])!={candidates[i]['entity'] for i in indices}:raise ValueError('Declared answer mapping differs')
        checked.append({'id':row['id'],'seed':row['seed'],'variant':row['variant'],'status':'representation/state ledger PASS'})
    return {'scope':'Offline source-state/request/declaration integrity, NOT semantic certification, calibration or new experiments',
        'records':len(rows),'question_seed_prefixes':len(packets),'checks':checked,'semantic_validity':'not assessed'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);args=parser.parse_args()
    print(json.dumps(check(args.folder),indent=2))
