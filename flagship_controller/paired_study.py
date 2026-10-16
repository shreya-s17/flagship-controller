"""Prospectively frozen paired development comparison; never reads gold labels."""
import argparse
import hashlib
import json
import platform
import random
import re
import time
from pathlib import Path
from . import structured_runtime as runtime
from .webqsp_runtime import post_json


def freeze(inputs,output,ids,model,snapshot):
    if output.exists():raise ValueError('Use a new output directory')
    records=[json.loads(x) for x in inputs.read_text().splitlines() if x.strip()]
    if any(set(r)-{'id','question','split'} for r in records):raise ValueError('Question-only inputs required')
    selected=[r for r in records if r['id'] in ids]
    if len(selected)!=len(ids) or len(set(ids))!=len(ids):raise ValueError('Missing or duplicate selected IDs')
    if any(r.get('split')!='pilot' for r in selected):raise ValueError('This first study is pilot-only; not official test')
    order=[];rng=random.Random(17)
    for r in selected:
        variants=['fixed','repair'];rng.shuffle(variants)
        order.extend({'id':r['id'],'variant':v} for v in variants)
    source=Path(runtime.__file__);transport=source.with_name('webqsp_runtime.py')
    plan={'status':'prospective exploratory pilot; not confirmatory or paper-final','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'input_sha256':hashlib.sha256(inputs.read_bytes()).hexdigest(),'question_ids':ids,'order':order,
          'runtime_version':runtime.VERSION,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'transport_sha256':hashlib.sha256(transport.read_bytes()).hexdigest(),'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'model':model,'snapshot':snapshot,'seed':17,'inference_options':{'temperature':0,'seed':17,'context_from_alias':4096,'threads_from_alias':4,'max_output_tokens':512},'limits':{'model_calls':10,'observed_tokens':16000,'graph_calls':80,'rows':100,'seconds_admission':600,'model_timeout':120,'graph_timeout':30,'max_observed_prompt_tokens':3000},
          'contrast':'one plan vs up to two plans with acquired join evidence and failure feedback; all other parsing/compiler/gates shared',
          'analysis':'paired question-level F1/EM, coverage, observed token/graph/time costs; exploratory paired bootstrap. No equal-realized-cost or calibrated reliability claim.',
          'stop_labels':'not identifiable without independent feasible-continuation audit','external_baseline':'not included; internal controls only',
          'model_digest_required':'ba6d123a5e5b0dfbab6a8aa2da25ca2643edaf4489953cd6f963e9482c4972fd',
          'python':platform.python_version(),'test_execution':False}
    output.mkdir(parents=True)
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    (output/'inputs.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in selected))
    (output/'runtime-source.py').write_bytes(source.read_bytes());(output/'transport-source.py').write_bytes(transport.read_bytes());(output/'harness-source.py').write_bytes(Path(__file__).read_bytes())
    return plan


def execute(folder,endpoint,model_url):
    plan=json.loads((folder/'plan.json').read_text());source=Path(runtime.__file__)
    for path,key in [(source,'source_sha256'),(source.with_name('webqsp_runtime.py'),'transport_sha256'),(Path(__file__),'harness_sha256')]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=plan[key]:raise ValueError('Frozen source changed: '+key)
    import urllib.request
    tags_url=model_url.rsplit('/api/',1)[0]+'/api/tags'
    with urllib.request.urlopen(tags_url,timeout=10) as response:tags=json.load(response)
    models=[m for m in tags['models'] if m['name'] in (plan['model'],plan['model']+':latest')]
    if len(models)!=1 or models[0]['digest']!=plan['model_digest_required']:raise ValueError('Model digest mismatch')
    (folder/'model-verification.json').write_text(json.dumps(models[0],indent=2)+'\n')
    show=post_json(model_url.rsplit('/api/',1)[0]+'/api/show',{'model':plan['model']},10)
    params=show.get('parameters','')
    if not re.search(r'num_ctx\s+4096\b',params) or not re.search(r'num_thread\s+4\b',params):
        raise ValueError('Frozen context/thread parameters changed')
    (folder/'model-configuration.json').write_text(json.dumps({'parameters':params,'details':show.get('details'),
        'template_sha256':hashlib.sha256(show.get('template','').encode()).hexdigest()},indent=2)+'\n')
    (folder/'execution-environment.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'runtime_version':runtime.VERSION},indent=2)+'\n')
    records={r['id']:r for r in map(json.loads,(folder/'inputs.jsonl').read_text().splitlines())}
    if (folder/'predictions.jsonl').exists():raise ValueError('Refuse to overwrite an executed or interrupted run')
    with (folder/'predictions.jsonl').open('w') as output,(folder/'progress.jsonl').open('w') as progress:
        for item in plan['order']:
            def event(e):
                progress.write(json.dumps({**item,**e})+'\n');progress.flush()
            result=runtime.run(records[item['id']],runtime.StructuredGraph(endpoint,plan['snapshot'],max_calls=80),
                runtime.StructuredModel(model_url,plan['model'],max_calls=10,max_tokens=16000),item['variant'],on_event=event)
            output.write(json.dumps(result)+'\n');output.flush()
            print(item['id'],item['variant'],result['terminal'],result['reason'],flush=True)
    (folder/'completion.json').write_text(json.dumps({'completed_pairs':len(records),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})+'\n')


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--inputs',type=Path,required=True);f.add_argument('--output',type=Path,required=True);f.add_argument('--ids',nargs='+',required=True)
    f.add_argument('--model',default='flagship-qwen2.5-7b-q4km');f.add_argument('--snapshot',required=True)
    e=sub.add_parser('execute');e.add_argument('folder',type=Path);e.add_argument('--endpoint',default='http://127.0.0.1:8891/sparql');e.add_argument('--model-url',default='http://127.0.0.1:11434/api/chat')
    a=p.parse_args()
    if a.command=='freeze':print(json.dumps(freeze(a.inputs,a.output,a.ids,a.model,a.snapshot),indent=2))
    else:execute(a.folder,a.endpoint,a.model_url)
if __name__=='__main__':main()
