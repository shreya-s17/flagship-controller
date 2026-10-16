"""Offline restoration of the exact recorded parse/link state for both methods.

Stops before any new request. This tests a common-state study building block;
it is not a larger-study executor, new performance data or fresh latency evidence.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from . import common_linker,semantic_runtime,structured_runtime,webqsp_runtime
from .webqsp_runtime import Blocked,NS

BOUNDARY={'PARSE','LINK','DISAMBIGUATE','EXCLUDE_ANSWER_CATEGORY'}
SOURCES={'linker-source.py':common_linker,'semantic-source.py':semantic_runtime,
    'parent-source.py':structured_runtime,'transport-source.py':webqsp_runtime}


def extract(study,question_id,variant='semantic-common-link'):
    study=Path(study);plan=json.loads((study/'manifest.json').read_text())
    for name,module in SOURCES.items():
        expected=plan['source_hashes'][name]
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()!=expected:
            raise ValueError('Current linking source differs: '+name)
        if hashlib.sha256((study/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Archived linking source mismatch: '+name)
    data=(study/'inputs.jsonl').read_bytes()
    if hashlib.sha256(data).hexdigest()!=plan['input_sha256']:raise ValueError('Input mismatch')
    records=[json.loads(line) for line in data.decode().splitlines() if line.strip()]
    record=next(r for r in records if r['id']==question_id)
    raw=(study/'predictions.jsonl').read_bytes()
    rows=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if [(r['id'],r['variant']) for r in rows]!=[(r['id'],r['variant']) for r in plan['order']]:
        raise ValueError('Incomplete recorded study')
    if json.loads((study/'completion.json').read_text())['completed']!=len(rows):raise ValueError('Completion mismatch')
    row=next(r for r in rows if r['id']==question_id and r['variant']==variant)
    events=[]
    for event in row['trace']:
        if event['action'] not in BOUNDARY:break
        events.append(copy.deepcopy(event))
    if not events:raise ValueError('No recorded linking prefix')
    cost=events[-1]['cost'];graph=row['graph_audit'][:cost['graph_calls']];model=row['model_audit'][:cost['model_calls']]
    if len(graph)!=cost['graph_calls'] or len(model)!=cost['model_calls']:
        raise ValueError('Incomplete prefix audit')
    if sum(m['input_tokens']+m['output_tokens'] for m in model)!=cost['model_tokens']:
        raise ValueError('Prefix usage mismatch')
    return {'record':record,'events':events,'graph_audit':graph,'model_audit':model,'cost':cost,
        'snapshot':plan['snapshot'],'model':plan['model'],'source_predictions_sha256':hashlib.sha256(raw).hexdigest(),
        'scope':'offline recorded linking restoration; no new requests; no end-to-end latency claim'}


class ReplayGraph(common_linker.LinkingGraph):
    def __init__(self,prefix):
        super().__init__('offline://no-network',prefix['snapshot'],max_calls=80)
        self.saved=copy.deepcopy(prefix['graph_audit']);self.cursor=0
    def select(self,body):
        if self.cursor>=len(self.saved):raise Blocked('offline_link_prefix_boundary')
        saved=self.saved[self.cursor]
        if saved['query']!='PREFIX ns: <'+NS+'>\n'+body:raise Blocked('link_prefix_graph_mismatch')
        if self.calls>=self.max_calls:raise Blocked('graph_budget')
        self.cursor+=1;self.calls+=1
        self.audit.append({**copy.deepcopy(saved),'replayed_prefix':True})
        if (saved.get('sql_state') or '00000').strip()!='00000':raise Blocked('graph_incomplete_sql_state')
        if len(saved['rows'])>self.row_limit:raise Blocked('graph_result_truncated')
        return copy.deepcopy(saved['rows'])


class ReplayModel(common_linker.SemanticModel):
    def __init__(self,prefix,graph):
        super().__init__('offline://no-network',prefix['model'],graph=graph,max_calls=10,max_tokens=16000)
        self.saved=copy.deepcopy(prefix['model_audit']);self.cursor=0
    def value(self,instruction,inputs):
        if self.cursor>=len(self.saved):raise Blocked('offline_link_prefix_boundary')
        saved=self.saved[self.cursor]
        prompt=json.dumps({'instruction':instruction,'inputs':inputs},sort_keys=True)
        if hashlib.sha256(prompt.encode()).hexdigest()!=saved['prompt_sha256']:
            raise Blocked('link_prefix_model_mismatch')
        if self.calls>=self.max_calls or self.tokens>=self.max_tokens:raise Blocked('model_budget')
        self.cursor+=1;self.calls+=1;self.tokens+=saved['input_tokens']+saved['output_tokens']
        self.audit.append({**copy.deepcopy(saved),'replayed_prefix':True})
        if saved['input_tokens']>3000:raise Blocked('model_context_budget_exceeded_after_call')
        if self.tokens>self.max_tokens:raise Blocked('model_budget_exceeded_after_call')
        return json.loads(saved['response'])
    def direct(self,instruction,inputs,schema):
        return self.value(instruction,inputs)
    def ask(self,instruction,inputs):
        if instruction.startswith('Choose only'):
            if self.contract is None:raise Blocked('missing_contract_state')
            return self.value(instruction,{**inputs,'question_contract':self.contract})
        if not instruction.startswith('Extract all'):raise Blocked('offline_link_prefix_boundary')
        # Original contract validation and state initialization still execute.
        return super().ask(instruction,inputs)


def verify(prefix,upstream):
    from .tog_adapter import run as baseline
    expected=[{k:v for k,v in e.items() if k not in ('step','cost')} for e in prefix['events']]
    results=[]
    for method in ('structured','baseline'):
        graph=ReplayGraph(prefix);model=ReplayModel(prefix,graph)
        if method=='structured':result=common_linker.semantic_run(prefix['record'],graph,model,variant='fixed')
        else:result=baseline(prefix['record'],graph,model,upstream)
        events=[]
        for event in result['trace']:
            if event['action'] not in BOUNDARY:break
            events.append({k:v for k,v in event.items() if k not in ('step','cost')})
        if events!=expected or graph.cursor!=len(graph.saved) or model.cursor!=len(model.saved):
            raise ValueError('Link state not reproduced: '+method)
        if any(result['cost'][k]!=prefix['cost'][k] for k in ('model_calls','model_tokens','graph_calls')):
            raise ValueError('Prefix resource accounting differs: '+method)
        if result['reason'] not in ('offline_link_prefix_boundary','entity_not_found','unsupported_parse',
                'no_named_anchor','unresolved_entity','missing_obligations','invalid_topic_mention'):
            raise ValueError('Unexpected replay terminal: '+result['reason'])
        results.append({'method':method,'equivalent_link_events':True,'replayed_model_calls':model.cursor,
            'replayed_graph_calls':graph.cursor,'physical_new_requests':0,'reason':result['reason']})
    return {'id':prefix['record']['id'],'source_predictions_sha256':prefix['source_predictions_sha256'],
        'scope':prefix['scope'],'checks':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('study',type=Path);parser.add_argument('--upstream',type=Path,required=True)
    args=parser.parse_args();plan=json.loads((args.study/'manifest.json').read_text())
    print(json.dumps([verify(extract(args.study,qid),args.upstream) for qid in plan['question_ids']],indent=2))
