"""Shared-state development study primitives; no labels or scoring imports.

Explicit per-instance seeded transport avoids global monkeypatching. Legacy
source is preserved; the local ask implementation retains its admission rules.
"""
import copy
import hashlib
import json
import time
from . import common_linker,semantic_runtime,structured_runtime,webqsp_runtime
from .webqsp_runtime import Ollama,Blocked,NS

VERSION='common-state-runtime-v1'
POLICIES=('fixed','repair','semantic-gate-off','reason-text-off','tog-explicit-final')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


class SeededOllama(Ollama):
    def ask(self,instruction,inputs):
        if self.calls>=self.max_calls or self.tokens>=self.max_tokens:raise Blocked('model_budget')
        self.calls+=1;prompt=json.dumps({'instruction':instruction,'inputs':inputs},sort_keys=True)
        started=time.perf_counter()
        if len(prompt.encode())>64000:raise Blocked('model_context_cap')
        response=self.send_json(self.url,{'model':self.model,'stream':False,
            'format':getattr(self,'response_format','json'),'messages':[{'role':'user','content':prompt}],
            'options':{'temperature':0,'seed':self.seed,'num_predict':min(512,self.max_tokens-self.tokens)}},self.timeout)
        usage=[response.get('prompt_eval_count'),response.get('eval_count')]
        if any(type(x) is not int or x<0 for x in usage):raise Blocked('model_usage_unavailable')
        self.tokens+=sum(usage)
        self.audit.append({'prompt_version':getattr(self,'prompt_version',VERSION),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
            'prompt':json.loads(prompt),'response':response.get('message',{}).get('content'),
            'input_tokens':usage[0],'output_tokens':usage[1],'elapsed_seconds':time.perf_counter()-started,'seed':self.seed})
        if usage[0]>getattr(self,'max_prompt_tokens',float('inf')):raise Blocked('model_context_budget_exceeded_after_call')
        if self.tokens>self.max_tokens:raise Blocked('model_budget_exceeded_after_call')
        try:return json.loads(response['message']['content'])
        except (KeyError,TypeError,json.JSONDecodeError) as exc:raise Blocked('invalid_model_json') from exc


class StudyStructured(structured_runtime.StructuredModel,SeededOllama):pass


class StudyModel(semantic_runtime.SemanticModel,StudyStructured):
    def __init__(self,*args,seed=17,policy='repair',prefix=None,**kwargs):
        super().__init__(*args,**kwargs)
        if type(seed) is not int or seed not in (17,29,43):raise ValueError('Unsupported study seed')
        if policy not in POLICIES:raise ValueError('Unknown study policy')
        self.seed=seed;self.policy=policy;self.provider_audit=[]
        self.prefix=copy.deepcopy(prefix or []);self.cursor=0;self.physical_attempts=0
    def send_json(self,url,payload,timeout):
        if payload['options']['seed']!=self.seed:raise Blocked('study_seed_mismatch')
        request={'payload':copy.deepcopy(payload),'payload_sha256':digest(payload),'seed':self.seed}
        if self.cursor<len(self.prefix):
            saved=self.prefix[self.cursor]
            if digest(payload)!=saved['payload_sha256']:raise Blocked('shared_state_model_mismatch')
            if 'response' not in saved:raise Blocked('unreplayable_provider_failure')
            self.cursor+=1;request.update(response=copy.deepcopy(saved['response']),replayed=True,elapsed_seconds=0.)
            self.provider_audit.append(request);return copy.deepcopy(saved['response'])
        self.physical_attempts+=1;started=time.perf_counter()
        try:
            response=webqsp_runtime.post_json(url,payload,timeout)
            request.update(response=copy.deepcopy(response),replayed=False);return response
        except (OSError,ValueError,KeyError,TypeError) as exc:
            request.update(error_type=type(exc).__name__,replayed=False);raise
        finally:
            request['elapsed_seconds']=time.perf_counter()-started;self.provider_audit.append(request)
    def direct(self,instruction,inputs,schema):
        self.timeout=120;self.max_prompt_tokens=3000;self.prompt_version=VERSION;self.response_format=schema
        return SeededOllama.ask(self,instruction,inputs)
    def ask(self,instruction,inputs):
        if instruction.startswith('Audit whether') and self.policy=='semantic-gate-off':
            self.semantic_audit.append({'action':'SEMANTIC_GATE_DISABLED','limitation':'Compiler/witness/type/resource guards retained'})
            return {'supported':True,'reason':'experiment disables only final model semantic audit','missing_obligations':[]}
        if instruction.startswith('Choose a program') and self.policy=='reason-text-off' and inputs.get('previous_failures'):
            inputs=copy.deepcopy(inputs)
            for failure in inputs['previous_failures']:failure['reason']='[withheld]'
            instruction=instruction.replace('Use observed failure feedback to revise the choice.','Revise the choice without rejection-reason text.')
            self.semantic_audit.append({'action':'REJECTION_REASON_TEXT_WITHHELD','limitation':'Failed-program masking and join acquisition remain'})
        return super().ask(instruction,inputs)


class StudyGraph(common_linker.LinkingGraph):
    def __init__(self,*args,prefix=None,link_ready=None,**kwargs):
        super().__init__(*args,**kwargs);self.saved=copy.deepcopy(prefix or []);self.cursor=0;self.link_ready=link_ready
    def inventory(self,node):
        if self.link_ready:
            callback=self.link_ready;self.link_ready=None;callback()
        return super().inventory(node)
    def select(self,body):
        if self.cursor>=len(self.saved):return super().select(body)
        saved=self.saved[self.cursor]
        if saved['query']!='PREFIX ns: <'+NS+'>\n'+body:raise Blocked('shared_state_graph_mismatch')
        if self.calls>=self.max_calls:raise Blocked('graph_budget')
        self.cursor+=1;self.calls+=1;self.audit.append({**copy.deepcopy(saved),'replayed_prefix':True})
        if (saved.get('sql_state') or '00000').strip()!='00000':raise Blocked('graph_incomplete_sql_state')
        if len(saved['rows'])>self.row_limit:raise Blocked('graph_result_truncated')
        return copy.deepcopy(saved['rows'])


def capture(record,endpoint,model_url,model_name,snapshot,seed,on_event=None):
    started=time.perf_counter();link=None
    graph=StudyGraph(endpoint,snapshot,max_calls=80)
    model=StudyModel(model_url,model_name,graph=graph,seed=seed,max_calls=10,max_tokens=16000)
    def state():
        return {'graph_audit':copy.deepcopy(graph.audit),'provider_audit':copy.deepcopy(model.provider_audit),
            'model_audit':copy.deepcopy(model.audit),'seconds':time.perf_counter()-started,
            'cost':{'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens}}
    def linked():
        nonlocal link
        link=state()
    graph.link_ready=linked
    def event(item):
        if on_event:on_event(item)
        if item['action']=='PLAN':
            if time.perf_counter()-started>600:raise Blocked('wall_time_budget')
            raise Blocked('shared_state_capture_boundary')
    result=common_linker.semantic_run(record,graph,model,variant='fixed',on_event=event)
    return {'record':record,'seed':seed,'model':model_name,'snapshot':snapshot,'link':link,
        'internal':state(),'internal_ready':result['reason']=='shared_state_capture_boundary',
        'capture_result':result,'provider_audit':model.provider_audit,
        'scope':'Gold-free common prefix; capture sentinel is not a policy prediction'}


def continue_policy(packet,policy,endpoint,model_url,upstream,on_event=None):
    if policy not in POLICIES:raise ValueError('Unknown policy')
    baseline=policy=='tog-explicit-final';prefix=packet['link'] if baseline else packet['internal']
    ready=prefix is not None if baseline else packet['internal_ready']
    if not ready:
        result=copy.deepcopy(packet['capture_result']);result['variant']=policy
        result['cost'].update(physical_new_graph_calls=0,physical_new_model_calls=0,
            charged_common_prefix_seconds=result['cost']['elapsed_seconds'],physical_execution_seconds=0.)
        result['shared_state']={'failure_shared_before_policy':True,'seed':packet['seed']}
        result['provider_audit']=copy.deepcopy(packet['provider_audit'])
        result['policy_continuation_executed']=False
        return result
    graph=StudyGraph(endpoint,packet['snapshot'],prefix=prefix['graph_audit'],max_calls=80)
    model=StudyModel(model_url,packet['model'],graph=graph,seed=packet['seed'],policy=policy,
        prefix=prefix['provider_audit'],max_calls=10,max_tokens=16000)
    seconds=max(0.,600-prefix['seconds'])
    if baseline:
        from .explicit_tog_adapter import ExplicitAdapter,VERSION as explicit_version
        from .tog_adapter import run
        def factory(*args,**kwargs):return ExplicitAdapter(*args,seed=packet['seed'],**kwargs)
        result=run(packet['record'],graph,model,upstream,seconds,on_event,
            adapter_factory=factory,project_native=True,runtime_version=explicit_version)
    else:
        result=common_linker.semantic_run(packet['record'],graph,model,
            variant='fixed' if policy=='fixed' else 'repair',seconds=seconds,on_event=on_event)
    if graph.cursor!=len(graph.saved) or model.cursor!=len(model.prefix):raise ValueError('Shared prefix not completely replayed')
    if 'shared_state_model_mismatch' in result['reason'] or 'shared_state_graph_mismatch' in result['reason']:
        raise ValueError('Shared prefix mismatch; stop rather than record a policy result')
    actual=result['cost']['elapsed_seconds']
    result['cost'].update(physical_execution_seconds=actual,charged_common_prefix_seconds=prefix['seconds'],
        elapsed_seconds=prefix['seconds']+actual,physical_new_graph_calls=graph.calls-graph.cursor,
        physical_new_model_calls=model.physical_attempts)
    result.update(variant=policy,provider_audit=model.provider_audit,
        shared_state={'replayed_graph_calls':graph.cursor,'replayed_model_calls':model.cursor,
            'seed':packet['seed'],'prefix_kind':'link' if baseline else 'through_first_plan',
            'latency':'original prefix plus current execution; not fresh end-to-end latency'},
        semantic_gate_enabled=policy!='semantic-gate-off',policy_continuation_executed=True)
    if policy=='semantic-gate-off' and result['terminal']=='ANSWER':result['reason']='observed_conjunctive_support; semantic_gate_bypassed_by_ablation'
    return result
