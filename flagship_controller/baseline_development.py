"""Freeze and execute a small development-only baseline sanity comparison.

Reserved training and official test inputs are refused. No evaluator imports.
"""
import argparse
import hashlib
import json
import platform
import random
import re
import time
import urllib.request
from pathlib import Path
from . import common_linker, semantic_runtime, structured_runtime, webqsp_runtime, tog_adapter, compact_tog_adapter

MODEL_DIGEST='ba6d123a5e5b0dfbab6a8aa2da25ca2643edaf4489953cd6f963e9482c4972fd'
MODULES={'harness-source.py':Path(__file__), 'linker-source.py':Path(common_linker.__file__),
    'semantic-source.py':Path(semantic_runtime.__file__), 'parent-source.py':Path(structured_runtime.__file__),
    'transport-source.py':Path(webqsp_runtime.__file__), 'adapter-source.py':Path(tog_adapter.__file__),
    'compact-adapter-source.py':Path(compact_tog_adapter.__file__)}


def freeze(inputs,output,upstream,snapshot,model='flagship-qwen2.5-7b-q4km',adapter='upstream-full'):
    if adapter not in ('upstream-full','compact-projected'):raise ValueError('Invalid adapter')
    if output.exists():raise ValueError('New output directory required')
    records=[json.loads(x) for x in inputs.read_text().splitlines() if x.strip()]
    if not 1<=len(records)<=10 or any(set(r)!={'id','question','split'} or r['split']!='pilot' or not isinstance(r['id'],str) or not isinstance(r['question'],str) or not r['question'].strip() for r in records):
        raise ValueError('One to ten pilot-only question records required; reserved/test inputs refused')
    if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate IDs')
    tog_adapter.load_upstream(upstream)
    if not snapshot:raise ValueError('Snapshot required')
    rng=random.Random(17);order=[]
    for record in records:
        methods=['semantic-common-link','tog-local' if adapter=='upstream-full' else 'tog-compact-projected'];rng.shuffle(methods)
        order.extend({'id':record['id'],'variant':method} for method in methods)
    plan={'status':'frozen development sanity check, NOT representative or held-out evaluation',
        'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'question_ids':[r['id'] for r in records],
        'order':order,'snapshot':snapshot,'model':model,'model_digest_required':MODEL_DIGEST,
        'input_sha256':hashlib.sha256(inputs.read_bytes()).hexdigest(),
        'source_hashes':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in MODULES.items()},
        'upstream_commit':tog_adapter.UPSTREAM_COMMIT,'upstream_hashes':tog_adapter.HASHES,'adapter':adapter,
        'limits':{'model_calls':10,'observed_model_tokens':16000,'graph_calls':80,'row_limit':100,
            'seconds_admission':600,'model_timeout':120,'graph_timeout':30,'max_observed_prompt_tokens':3000},
        'inference_options':{'temperature':0,'seed':17,'context':4096,'threads':4,'max_output_tokens':512},
        'baseline_search':{'width':3,'depth':3,'entity_sample_if_at_least':20,'sample_size':5},
        'relation_presentation':'full upstream inventory' if adapter=='upstream-full' else 'additional question-lexical top32 relation presentation; may omit necessary relations',
        'answer_projection':'strict braced unique observed name mapping' if adapter=='upstream-full' else 'extra charged constrained model call; final-beam candidates only, verbatim response quotes with full observed names required',
        'analysis':'Official ID-set metrics only on original training questions; handwritten inverse and no-match controls unscored. Retain native baseline text and mapping failures. Same maximum admission budgets, not equal realized costs. No faithful published-model reproduction or semantic proof.',
        'common_linker':'Identical model/graph linking implementations; fresh separate executions, not forced identical sampled outputs. Costs charged to each method.',
        'upstream_distribution':'Separate pinned source required; no vendored source. Public redistribution/license resolution remains open.',
        'python':platform.python_version(),'reserved_cohort_execution':False,'official_test_execution':False}
    output.mkdir(parents=True)
    (output/'manifest.json').write_text(json.dumps(plan,indent=2)+'\n')
    (output/'inputs.jsonl').write_bytes(inputs.read_bytes())
    for name,path in MODULES.items():(output/name).write_bytes(path.read_bytes())
    return plan


def execute(folder,upstream,endpoint,model_url):
    plan=json.loads((folder/'manifest.json').read_text())
    for name,path in MODULES.items():
        expected=plan['source_hashes'][name]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected or hashlib.sha256((folder/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen source mismatch: '+name)
    if hashlib.sha256((folder/'inputs.jsonl').read_bytes()).hexdigest()!=plan['input_sha256']:raise ValueError('Frozen input mismatch')
    tog_adapter.load_upstream(upstream)
    if plan['upstream_hashes']!=tog_adapter.HASHES:raise ValueError('Upstream hash plan mismatch')
    if (folder/'predictions.jsonl').exists():raise ValueError('Refuse overwrite of started run')
    base_url=model_url.rsplit('/api/',1)[0]
    with urllib.request.urlopen(base_url+'/api/tags',timeout=10) as response:tags=json.load(response)
    models=[m for m in tags['models'] if m['name'] in (plan['model'],plan['model']+':latest')]
    if len(models)!=1 or models[0]['digest']!=plan['model_digest_required']:raise ValueError('Model digest mismatch')
    show=webqsp_runtime.post_json(base_url+'/api/show',{'model':plan['model']},10)
    params=show.get('parameters','')
    if not re.search(r'num_ctx\s+4096\b',params) or not re.search(r'num_thread\s+4\b',params):raise ValueError('Model context/thread mismatch')
    (folder/'model-verification.json').write_text(json.dumps({'model':models[0],'parameters':params,'template_sha256':hashlib.sha256(show.get('template','').encode()).hexdigest()},indent=2)+'\n')
    (folder/'execution-environment.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform()},indent=2)+'\n')
    records={r['id']:r for r in map(json.loads,(folder/'inputs.jsonl').read_text().splitlines())}
    if list(records)!=plan['question_ids']:raise ValueError('Frozen question order mismatch')
    with (folder/'predictions.jsonl').open('x') as output,(folder/'progress.jsonl').open('x') as progress:
        for item in plan['order']:
            record=records[item['id']]
            graph=common_linker.LinkingGraph(endpoint,plan['snapshot'],max_calls=80)
            model=common_linker.SemanticModel(model_url,plan['model'],graph=graph,max_calls=10,max_tokens=16000)
            def event(e):
                progress.write(json.dumps({**item,**e})+'\n');progress.flush()
            if item['variant']=='tog-local':result=tog_adapter.run(record,graph,model,upstream,on_event=event)
            elif item['variant']=='tog-compact-projected':result=compact_tog_adapter.run(record,graph,model,upstream,on_event=event)
            else:result=common_linker.semantic_run(record,graph,model,on_event=event)
            result['variant']=item['variant'];result['linker_version']=common_linker.VERSION
            output.write(json.dumps(result)+'\n');output.flush()
            print(item['id'],item['variant'],result['terminal'],result['reason'],flush=True)
    (folder/'completion.json').write_text(json.dumps({'completed':len(plan['order']),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})+'\n')


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--inputs',type=Path,required=True);f.add_argument('--output',type=Path,required=True);f.add_argument('--upstream',type=Path,required=True);f.add_argument('--snapshot',required=True);f.add_argument('--adapter',choices=['upstream-full','compact-projected'],default='upstream-full')
    e=sub.add_parser('execute');e.add_argument('folder',type=Path);e.add_argument('--upstream',type=Path,required=True);e.add_argument('--endpoint',default='http://127.0.0.1:8891/sparql');e.add_argument('--model-url',default='http://127.0.0.1:11434/api/chat')
    args=parser.parse_args()
    if args.command=='freeze':print(json.dumps(freeze(args.inputs,args.output,args.upstream,args.snapshot,adapter=args.adapter),indent=2))
    else:execute(args.folder,args.upstream,args.endpoint,args.model_url)

if __name__=='__main__':main()
