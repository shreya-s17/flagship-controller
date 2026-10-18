"""V5 local baseline: constrained stop/answer declaration over observed nodes.

An additional prompting/decoding adaptation, not original-paper reproduction.
Constrained structure prevents missing fields, not wrong semantic decisions.
"""
import json
from . import tog_adapter as parent
from .indexed_tog_adapter import IndexedAdapter
from .structured_runtime import object_schema
from .webqsp_runtime import Blocked

VERSION='tog-declared-json-v5'


def select_declared(response,candidates):
    decision=response.get('decision');indices=response.get('answer_indices')
    if decision not in ('ANSWER','CONTINUE') or not isinstance(indices,list):raise Blocked('invalid_declared_decision')
    if len(indices)>len(candidates) or any(type(i) is not int or not 0<=i<len(candidates) for i in indices) or len(set(indices))!=len(indices):
        raise Blocked('invalid_declared_answer_indices')
    if (decision=='ANSWER')!=bool(indices):raise Blocked('inconsistent_declared_stop')
    return [candidates[i]['entity'] for i in indices]


class DeclaredAdapter(IndexedAdapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.native_stop=None;self.declaration=None
        def reasoning(question,chains,settings):
            candidates=[{'entity':node,'names':names} for node,names in sorted(self.names.items()) if names]
            if not candidates or len(candidates)>64:raise Blocked('declared_candidate_cap_or_empty')
            schema=object_schema({'decision':{'type':'string','enum':['ANSWER','CONTINUE']},
                'answer_indices':{'type':'array','maxItems':len(candidates),'uniqueItems':True,
                    'items':{'type':'integer','enum':list(range(len(candidates)))}},
                'reason':{'type':'string','maxLength':160}})
            response=self.model.direct('Decide whether the observed graph chains suffice to answer the question. If sufficient, decision ANSWER and select ALL AND ONLY the concluded answer entity indices from supplied observed nodes. Context names, historical alternatives and names merely quoted in the question are not answers. An answer may have appeared in an earlier chain, not only the last frontier. If insufficient, decision CONTINUE and empty answer_indices. Do not add facts. Return a concise reason. This is an uncalibrated model decision, not semantic proof.',
                {'question':question,'observed_chains':chains,
                    'candidates':[{'index':i,**candidate} for i,candidate in enumerate(candidates)]},schema)
            raw=self.model.audit[-1]['response']
            if json.loads(raw)!=response:raise Blocked('declared_response_ledger_mismatch')
            answers=select_declared(response,candidates)
            self.declaration={'raw':raw,'response':response,'candidates':candidates,'answers':answers}
            self.log('DECLARED_JSON_REASONING',candidates=candidates,response=response,
                limitation='Replaces native free-text stop prompt/parser with structured declaration; not semantic proof')
            return response['decision']=='ANSWER',raw
        self.ns['reasoning']=reasoning
    def search(self,*args):
        raw,chains,stop=super().search(*args);self.native_stop=stop
        return raw,chains,stop
    def project_answer(self,question,native,candidates):
        if self.native_stop!='reasoning_yes' or not self.declaration or native!=self.declaration['raw']:
            return [],'no_graph_reasoning_answer_declaration'
        self.log('DECLARED_JSON_MAPPING',answers=self.declaration['answers'],
            declaration=self.declaration['response'],model_call_skipped=True)
        return self.declaration['answers'],'exact_declared_index_mapping_not_semantic_certification'


def run(record,graph,model,upstream,seconds=600,on_event=None):
    return parent.run(record,graph,model,upstream,seconds,on_event,
        adapter_factory=DeclaredAdapter,project_native=True,runtime_version=VERSION)
