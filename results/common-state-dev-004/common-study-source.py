"""Frozen development-only common-state control study with a durable journal.

At most10 pilot questions; reserved/test input is refused. No evaluator imports.
Interrupted admitted work is retained as unknown-cost abstention, never retried.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import time
import urllib.request
from . import study_runtime as runtime
from . import common_linker,semantic_runtime,structured_runtime,webqsp_runtime
from . import tog_adapter,compact_tog_adapter,indexed_tog_adapter,explicit_tog_adapter,declared_json_tog_adapter

MODEL_DIGEST='ba6d123a5e5b0dfbab6a8aa2da25ca2643edaf4489953cd6f963e9482c4972fd'
MODULES={'common-study-source.py':Path(__file__),'study-runtime-source.py':Path(runtime.__file__),
    'linker-source.py':Path(common_linker.__file__),'semantic-source.py':Path(semantic_runtime.__file__),
    'parent-source.py':Path(structured_runtime.__file__),'transport-source.py':Path(webqsp_runtime.__file__),
    'adapter-source.py':Path(tog_adapter.__file__),'compact-adapter-source.py':Path(compact_tog_adapter.__file__),
    'indexed-adapter-source.py':Path(indexed_tog_adapter.__file__),'explicit-adapter-source.py':Path(explicit_tog_adapter.__file__),
    'declared-json-adapter-source.py':Path(declared_json_tog_adapter.__file__)}


def utc():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def sha(data):return hashlib.sha256(data).hexdigest()


def write_json(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w') as stream:
        stream.write(json.dumps(value,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def journal(folder,key,item,operation,interrupted):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    result=folder/(key+'.json');started=folder/(key+'.started.json');halted=folder/(key+'.halted.json')
    if halted.exists():raise ValueError('Integrity failure requires investigation: '+str(halted))
    if result.exists():
        saved=json.loads(result.read_text())
        if saved['item']!=item or saved['sha256']!=runtime.digest(saved['value']):raise ValueError('Committed journal mismatch')
        return saved['value']
    if started.exists():
        if json.loads(started.read_text())['item']!=item:raise ValueError('Started journal mismatch')
        value=interrupted()
    else:
        write_json(started,{'item':item,'started_utc':utc()})
        try:value=operation()
        except (ValueError,AssertionError) as exc:
            write_json(halted,{'item':item,'error':str(exc),'utc':utc()});raise
    write_json(result,{'item':item,'value':value,'sha256':runtime.digest(value)})
    return value


def interrupted_result(record,reason,prefix=None,progress=None):
    cost=copy.deepcopy(prefix['cost']) if prefix else {'graph_calls':0,'model_calls':0,'model_tokens':0}
    if progress and progress.exists():
        lines=progress.read_text().splitlines()
        for line in lines:
            try:event=json.loads(line)
            except json.JSONDecodeError:break
            for key in ('graph_calls','model_calls','model_tokens'):cost[key]=max(cost[key],event.get('cost',{}).get(key,0))
    cost.update(elapsed_seconds=prefix.get('seconds',0.) if prefix else 0.,model_usage_complete=False,
        cost_is_lower_bound=True,unreturned_request_usage_unknown=True,physical_new_model_calls=None,
        physical_new_graph_calls=None,elapsed_seconds_unknown=True)
    return {'id':record['id'],'split':record['split'],'terminal':'ABSTAIN','answers':[],'reason':reason,
        'trace':[],'witnesses':[],'model_audit':[],'graph_audit':[],'provider_audit':[],
        'cost':cost,'scope':'Interrupted admitted work retained; no retry, no invented zero actual cost'}


def freeze(inputs,output,upstream,snapshot,seeds=(17,29,43),directed_audit=False):
    inputs,output=Path(inputs),Path(output);data=inputs.read_bytes()
    records=[json.loads(line) for line in data.decode().splitlines() if line.strip()]
    if output.exists():raise ValueError('New output directory required')
    if not 1<=len(records)<=10 or any(set(r)!={'id','question','split'} or r['split']!='pilot' or
            not isinstance(r['id'],str) or not r['id'] or not isinstance(r['question'],str) or not r['question'].strip() for r in records):
        raise ValueError('Only1–10 question-only pilot records; reserved/test refused')
    if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate question IDs')
    if not seeds or len(set(seeds))!=len(seeds) or any(type(s) is not int or s not in (17,29,43) for s in seeds):raise ValueError('Invalid seeds')
    if type(directed_audit) is not bool:raise ValueError('Invalid directed audit option')
    if not snapshot:raise ValueError('Snapshot required')
    tog_adapter.load_upstream(upstream)
    rng=random.Random(113);order=[]
    for seed in seeds:
        for record in records:
            policies=list(runtime.POLICIES);rng.shuffle(policies)
            order.extend({'id':record['id'],'seed':seed,'variant':policy} for policy in policies)
    plan={'status':'Frozen development common-state study; NOT held-out or publication-ready evaluation',
        'directed_role_audit':directed_audit,'created_utc':utc(),'question_ids':[r['id'] for r in records],'seeds':list(seeds),'order':order,
        'input_sha256':sha(data),'source_hashes':{name:sha(path.read_bytes()) for name,path in MODULES.items()},
        'snapshot':snapshot,'model':'flagship-qwen2.5-7b-q4km','model_digest_required':MODEL_DIGEST,
        'upstream_commit':tog_adapter.UPSTREAM_COMMIT,'upstream_hashes':tog_adapter.HASHES,
        'budgets':{'model_calls':10,'returned_usage_tokens':16000,'graph_calls':80,'rows':100,'seconds_admission':600,
            'model_timeout':120,'graph_timeout':30,'max_observed_prompt_tokens':3000},
        'inference':{'temperature':0,'context':4096,'threads':4,'max_output_tokens':512,'sampling_seed_per_item':True,
            'python_hash_seed_required':'17','schedule_seed':113},
        'shared_state':'One captured parse/link per question/seed for all policies; internal controls also replay through the same first PLAN/catalog. Prefix usage/time charged to each; physical new requests reported separately.',
        'ablations':{'semantic-gate-off':'Only final same-model audit bypassed; compiler/witness/type/resource guards retained',
            'reason-text-off':'Only rejection-reason text withheld; failed-program masking and join acquisition remain'},
        'serialization':'raw RDF lexical strings / Freebase URI IDs; no calendar-date projection; known date mismatch retained',
        'failure_accounting':'Full planned denominator; no retry of interrupted admitted work; unknown usage reported as lower bound. Integrity mismatch halts the study.',
        'baseline':'Constrained combined stop/answer-index declaration over all observed names; indexed relations; not original-paper reproduction',
        'analysis':'Offline official ID-set F1/exact on original training questions only. Handwritten controls unscored. Repeated seeds clustered by question. No significance/generalization or semantic guarantee inferred.',
        'reserved_execution':False,'official_test_execution':False,'independent_review_completed':False}
    output.mkdir(parents=True);write_json(output/'manifest.json',plan);(output/'inputs.jsonl').write_bytes(data)
    for name,path in MODULES.items():(output/name).write_bytes(path.read_bytes())
    return plan


def execute(folder,upstream,endpoint,model_url):
    folder=Path(folder);plan=json.loads((folder/'manifest.json').read_text())
    for name,path in MODULES.items():
        if sha(path.read_bytes())!=plan['source_hashes'][name] or sha((folder/name).read_bytes())!=plan['source_hashes'][name]:
            raise ValueError('Frozen source mismatch: '+name)
    if sha((folder/'inputs.jsonl').read_bytes())!=plan['input_sha256']:raise ValueError('Frozen input mismatch')
    if os.environ.get('PYTHONHASHSEED')!='17':raise ValueError('Set PYTHONHASHSEED=17 before starting Python')
    tog_adapter.load_upstream(upstream)
    if tog_adapter.HASHES!=plan['upstream_hashes']:raise ValueError('Upstream plan mismatch')
    records={r['id']:r for r in map(json.loads,(folder/'inputs.jsonl').read_text().splitlines())}
    if list(records)!=plan['question_ids']:raise ValueError('Input order mismatch')
    actual=[(item['id'],item['seed'],item['variant']) for item in plan['order']]
    expected={(qid,seed,policy) for qid in records for seed in plan['seeds'] for policy in runtime.POLICIES}
    if len(actual)!=len(expected) or set(actual)!=expected:raise ValueError('Incomplete or duplicate planned policy order')
    if (folder/'completion.json').exists():
        completed=json.loads((folder/'completion.json').read_text())
        raw=(folder/'predictions.jsonl').read_bytes()
        if completed['completed']!=len(actual) or completed['predictions_sha256']!=sha(raw):raise ValueError('Completed output mismatch')
        print('Already complete; no requests repeated',flush=True);return
    root=model_url.rsplit('/api/',1)[0]
    with urllib.request.urlopen(root+'/api/tags',timeout=10) as response:tags=json.load(response)
    matches=[m for m in tags['models'] if m['name'] in (plan['model'],plan['model']+':latest')]
    if len(matches)!=1 or matches[0]['digest']!=plan['model_digest_required']:raise ValueError('Model digest mismatch')
    show=webqsp_runtime.post_json(root+'/api/show',{'model':plan['model']},10)
    import re
    if not re.search(r'num_ctx\s+4096\b',show.get('parameters','')) or not re.search(r'num_thread\s+4\b',show.get('parameters','')):
        raise ValueError('Model configuration mismatch')
    verification={'model':matches[0],'parameters':show['parameters'],'template_sha256':sha(show.get('template','').encode()),
        'python':platform.python_version(),'platform':platform.platform()}
    if (folder/'model-verification.json').exists():
        if json.loads((folder/'model-verification.json').read_text())!=verification:raise ValueError('Execution environment changed across resume')
    else:write_json(folder/'model-verification.json',verification)
    jobs=folder/'journal';jobs.mkdir(exist_ok=True);results=[]
    def observer(path):
        def log(event):
            with path.open('a') as stream:
                stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
        return log
    for index,item in enumerate(plan['order']):
        record=records[item['id']];seed=item['seed'];key=str(seed)+'-'+sha(item['id'].encode())[:16]
        prefix_progress=jobs/(key+'-prefix.progress.jsonl')
        def interrupted_capture():
            result=interrupted_result(record,'interrupted_common_prefix_unknown_usage',progress=prefix_progress)
            return {'record':record,'seed':seed,'model':plan['model'],'snapshot':plan['snapshot'],'link':None,
                'internal':None,'internal_ready':False,'capture_result':result,'provider_audit':[],
                'scope':'Interrupted common capture; propagate retained abstention to every policy'}
        packet=journal(jobs,key+'-prefix',{'id':record['id'],'seed':seed,'stage':'prefix'},
            lambda:runtime.capture(record,endpoint,model_url,plan['model'],plan['snapshot'],seed,observer(prefix_progress),directed_audit=plan.get('directed_role_audit',False)),interrupted_capture)
        policy_key=f'policy-{index:04d}';progress=jobs/(policy_key+'.progress.jsonl')
        prefix=packet['link'] if item['variant']=='tog-declared-json' else packet['internal']
        def interrupted_policy():
            result=interrupted_result(record,'interrupted_policy_unknown_usage',prefix,progress)
            result.update(variant=item['variant'],shared_state={'interrupted':True,'seed':seed});return result
        result=journal(jobs,policy_key,{**item,'prefix_sha256':runtime.digest(packet)},
            lambda:runtime.continue_policy(packet,item['variant'],endpoint,model_url,upstream,observer(progress)),interrupted_policy)
        result.update(variant=item['variant'],seed=seed);results.append(result)
        temporary=folder/'predictions.jsonl.tmp'
        with temporary.open('w') as stream:
            for row in results:stream.write(json.dumps(row)+'\n')
            stream.flush();os.fsync(stream.fileno())
        temporary.replace(folder/'predictions.jsonl')
        print(item['id'],seed,item['variant'],result['terminal'],result['reason'],flush=True)
    write_json(folder/'completion.json',{'completed':len(results),'predictions_sha256':sha((folder/'predictions.jsonl').read_bytes()),
        'question_seed_prefixes':len(plan['question_ids'])*len(plan['seeds']),
        'utc':utc(),'scope':'Completed development-only outcomes, including retained failures'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--inputs',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    f.add_argument('--upstream',type=Path,required=True);f.add_argument('--snapshot',required=True);f.add_argument('--seeds',type=int,nargs='+',default=[17,29,43]);f.add_argument('--directed-audit',action='store_true')
    e=sub.add_parser('execute');e.add_argument('folder',type=Path);e.add_argument('--upstream',type=Path,required=True)
    e.add_argument('--endpoint',default='http://127.0.0.1:8891/sparql');e.add_argument('--model-url',default='http://127.0.0.1:11434/api/chat');args=parser.parse_args()
    if args.command=='freeze':print(json.dumps(freeze(args.inputs,args.output,args.upstream,args.snapshot,args.seeds,args.directed_audit),indent=2))
    else:execute(args.folder,args.upstream,args.endpoint,args.model_url)
