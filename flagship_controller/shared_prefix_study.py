"""Follow-up policy replay from identical recorded, question-only initial states.

No gold labels. The original policy code is unchanged. Recorded prefix usage is
charged to both controls; only the repair continuation makes new requests.
Latency is explicitly a prefix-plus-continuation construction, not a fresh run.
"""
import argparse
import copy
import hashlib
import json
import re
import platform
import urllib.request
from pathlib import Path
import time
from unittest.mock import patch
from . import structured_runtime as runtime
from . import webqsp_runtime as transport


class PrefixModel(runtime.StructuredModel):
    def __init__(self,url,model,prefix):
        super().__init__(url,model,max_calls=10,max_tokens=16000)
        self.prefix=copy.deepcopy(prefix);self.cursor=0
    def ask(self,instruction,inputs):
        real=transport.post_json
        before=self.cursor
        def request(url,payload,timeout):
            if self.cursor>=len(self.prefix):return real(url,payload,timeout)
            saved=self.prefix[self.cursor]
            prompt=payload['messages'][0]['content']
            if hashlib.sha256(prompt.encode()).hexdigest()!=saved['prompt_sha256']:
                raise runtime.Blocked('shared_prefix_model_mismatch')
            self.cursor+=1
            return {'message':{'content':saved['response']},'prompt_eval_count':saved['input_tokens'],'eval_count':saved['output_tokens']}
        with patch.object(transport,'post_json',side_effect=request):
            value=super().ask(instruction,inputs)
        if self.cursor>before and self.audit:self.audit[-1]['replayed_prefix']=True
        return value


class PrefixGraph(runtime.StructuredGraph):
    def __init__(self,endpoint,snapshot,prefix):
        super().__init__(endpoint,snapshot,max_calls=80)
        self.prefix=copy.deepcopy(prefix);self.cursor=0
    def select(self,body):
        if self.cursor>=len(self.prefix):return super().select(body)
        saved=self.prefix[self.cursor]
        if saved['query']!='PREFIX ns: <'+runtime.NS+'>\n'+body:
            raise runtime.Blocked('shared_prefix_graph_mismatch')
        if self.calls>=self.max_calls:raise runtime.Blocked('graph_budget')
        self.cursor+=1;self.calls+=1
        row=copy.deepcopy(saved);row.update(replayed_prefix=True,elapsed_seconds=0.)
        self.audit.append(row)
        if (saved.get('sql_state') or '00000').strip()!='00000':raise runtime.Blocked('graph_incomplete_sql_state')
        if len(saved['rows'])>self.row_limit:raise runtime.Blocked('graph_result_truncated')
        return copy.deepcopy(saved['rows'])


def replay(record,baseline,endpoint,model_url,model,snapshot,variant):
    graph=PrefixGraph(endpoint,snapshot,baseline['graph_audit'])
    llm=PrefixModel(model_url,model,baseline['model_audit'])
    common_seconds=baseline['cost']['elapsed_seconds']
    result=runtime.run(record,graph,llm,variant=variant,seconds=max(0.,600-common_seconds))
    actual=result['cost']['elapsed_seconds']
    result['cost'].update(actual_replay_execution_seconds=actual,charged_common_prefix_seconds=common_seconds,
        elapsed_seconds=common_seconds+actual,physical_new_model_calls=llm.calls-llm.cursor,
        physical_new_graph_calls=graph.calls-graph.cursor)
    result['shared_prefix']={'model_responses_replayed':llm.cursor,'graph_results_replayed':graph.cursor,
                            'expected_model_responses':len(baseline['model_audit']),'expected_graph_results':len(baseline['graph_audit'])}
    return result


def freeze(original,destination):
    if destination.exists():raise ValueError('Use a new output directory')
    plan=json.loads((original/'plan.json').read_text())
    rows=[json.loads(x) for x in (original/'predictions.jsonl').read_text().splitlines()]
    if [(r['id'],r['variant']) for r in rows]!=[(r['id'],r['variant']) for r in plan['order']]:raise ValueError('Original run incomplete')
    baselines={r['id']:r for r in rows if r['variant']=='fixed'}
    excluded={qid:'incomplete recorded usage/query prefix' for qid,r in baselines.items()
              if r['cost']['model_calls']!=len(r['model_audit']) or r['cost']['graph_calls']!=len(r['graph_audit']) or r['cost']['elapsed_seconds']>=600}
    ids=[qid for qid in plan['question_ids'] if qid not in excluded]
    if not ids:raise ValueError('No replayable prefixes')
    if hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest()!=plan['source_sha256']:raise ValueError('Original runtime changed')
    if hashlib.sha256(Path(transport.__file__).read_bytes()).hexdigest()!=plan['transport_sha256']:raise ValueError('Original transport changed')
    follow={**plan,'status':'exploratory shared-prefix follow-up; not confirmatory','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'original_plan_sha256':hashlib.sha256((original/'plan.json').read_bytes()).hexdigest(),
      'original_predictions_sha256':hashlib.sha256((original/'predictions.jsonl').read_bytes()).hexdigest(),
      'question_ids':ids,'original_question_ids':plan['question_ids'],'excluded_prefixes':excluded,
      'order':[{'id':qid,'variant':v} for qid in ids for v in ('fixed','repair')],
      'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'contrast':'same recorded initial observations/model outputs; fixed stop vs bounded repair continuation',
      'analysis':'Shared prefix is replayed and its recorded resource cost charged to both; only continuation makes new requests. Latency is prefix plus continuation, not independently measured end-to-end latency.',
      'motivation':'Audit whether independent parsing differences confound the first pilot; frozen before this continuation, without reading gold outcomes.'}
    destination.mkdir(parents=True)
    (destination/'plan.json').write_text(json.dumps(follow,indent=2)+'\n')
    (destination/'inputs.jsonl').write_bytes((original/'inputs.jsonl').read_bytes())
    (destination/'fixed-prefixes.jsonl').write_text(''.join(json.dumps(baselines[qid])+'\n' for qid in ids))
    (destination/'runtime-source.py').write_bytes(Path(runtime.__file__).read_bytes())
    (destination/'transport-source.py').write_bytes(Path(transport.__file__).read_bytes())
    (destination/'harness-source.py').write_bytes(Path(__file__).read_bytes())
    return follow


def execute(folder,endpoint,model_url):
    plan=json.loads((folder/'plan.json').read_text())
    for path,key in [(Path(runtime.__file__),'source_sha256'),(Path(transport.__file__),'transport_sha256'),(Path(__file__),'harness_sha256')]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=plan[key]:raise ValueError('Frozen source changed')
    if (folder/'predictions.jsonl').exists():raise ValueError('Refuse overwrite')
    tags_url=model_url.rsplit('/api/',1)[0]+'/api/tags'
    with urllib.request.urlopen(tags_url,timeout=10) as response:tags=json.load(response)
    models=[m for m in tags['models'] if m['name'] in (plan['model'],plan['model']+':latest')]
    if len(models)!=1 or models[0]['digest']!=plan['model_digest_required']:raise ValueError('Model digest mismatch')
    show=transport.post_json(model_url.rsplit('/api/',1)[0]+'/api/show',{'model':plan['model']},10)
    params=show.get('parameters','')
    if not re.search(r'num_ctx\s+4096\b',params) or not re.search(r'num_thread\s+4\b',params):raise ValueError('Frozen context/thread parameters changed')
    (folder/'model-verification.json').write_text(json.dumps(models[0],indent=2)+'\n')
    (folder/'model-configuration.json').write_text(json.dumps({'parameters':params,'details':show.get('details'),
        'template_sha256':hashlib.sha256(show.get('template','').encode()).hexdigest()},indent=2)+'\n')
    (folder/'execution-environment.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'runtime_version':runtime.VERSION},indent=2)+'\n')
    baselines={r['id']:r for r in map(json.loads,(folder/'fixed-prefixes.jsonl').read_text().splitlines())}
    records={r['id']:r for r in map(json.loads,(folder/'inputs.jsonl').read_text().splitlines())}
    equivalence=[]
    with (folder/'predictions.jsonl').open('w') as output:
        for qid in plan['question_ids']:
            baseline=baselines[qid]
            control=replay(records[qid],baseline,endpoint,model_url,plan['model'],plan['snapshot'],'fixed')
            keys=('terminal','reason','answers','witnesses')
            matched=all(control[k]==baseline[k] for k in keys)
            matched=matched and all(control['cost'][k]==baseline['cost'][k] for k in ('model_calls','model_tokens','graph_calls'))
            matched=matched and control['cost']['physical_new_model_calls']==control['cost']['physical_new_graph_calls']==0
            if not matched:raise ValueError('Prefix replay not equivalent: '+qid)
            equivalence.append({'id':qid,'equivalent_fixed_replay':True,'physical_requests':0})
            output.write(json.dumps(baseline)+'\n');output.flush()
            result=replay(records[qid],baseline,endpoint,model_url,plan['model'],plan['snapshot'],'repair')
            output.write(json.dumps(result)+'\n');output.flush()
            print(qid,'repair',result['terminal'],result['reason'],flush=True)
    (folder/'equivalence-check.json').write_text(json.dumps(equivalence,indent=2)+'\n')
    (folder/'completion.json').write_text(json.dumps({'completed_pairs':len(equivalence),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})+'\n')


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('original',type=Path);f.add_argument('output',type=Path)
    e=sub.add_parser('execute');e.add_argument('folder',type=Path);e.add_argument('--endpoint',default='http://127.0.0.1:8891/sparql');e.add_argument('--model-url',default='http://127.0.0.1:11434/api/chat')
    a=p.parse_args()
    if a.command=='freeze':print(json.dumps(freeze(a.original,a.output),indent=2))
    else:execute(a.folder,a.endpoint,a.model_url)
if __name__=='__main__':main()
