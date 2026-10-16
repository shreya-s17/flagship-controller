"""Second, explicitly more adapted development baseline; v1 stays preserved.

Lexical top32 relation presentation accommodates the CPU context, and a charged
structured extraction maps explicit native conclusions to final beam endpoints.
This is NOT faithful ToG reproduction. No gold data or scorer is imported.
"""
import re
from . import tog_adapter as parent
from .structured_runtime import rank_relations
from .webqsp_runtime import Blocked

VERSION='tog-compact-projected-v2'


def validate_projection(response,candidates,native):
    if response.get('supported') is not True:return [],'native_answer_not_explicit'
    selections=response.get('selections')
    if not isinstance(selections,list) or not selections:return [],'missing_native_answer_selection'
    indices=[]
    for selection in selections:
        index=selection.get('index');quote=selection.get('quote')
        if type(index) is not int or not 0<=index<len(candidates) or index in indices:
            raise Blocked('invalid_native_answer_index')
        if not isinstance(quote,str) or not quote.strip() or quote not in native:
            raise Blocked('native_answer_quote_not_in_response')
        if not any(re.search(r'(?<!\w)'+re.escape(name.casefold())+r'(?!\w)',quote.casefold()) for name in candidates[index]['names']):
            raise Blocked('selected_name_not_in_native_quote')
        indices.append(index)
    return [candidates[i]['entity'] for i in indices],'charged_model_extraction_with_verbatim_name_quotes; not semantic proof'


class CompactAdapter(parent.Adapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        original=self.ns['construct_relation_prune_prompt']
        clean=self.ns['clean_relations'];self.presented=set()
        def prompt(question,entity,relations,settings):
            choices=[{'relation':r,'direction':'out'} for r in dict.fromkeys(relations)]
            names=[r['relation'] for r in rank_relations(question,choices,[],limit=32)]
            self.presented=set(names)
            self.log('RELATION_PRESENTATION',full_relations=relations,presented=names,
                cap=32,policy='question lexical ranking; direction still resolved by upstream head/tail sets',
                limitation='Additional adaptation; may exclude necessary relations')
            return original(question,entity,names,settings)
        def validated(text,node,head_relations):
            flag,choices=clean(text,node,head_relations)
            if flag and any(c['relation'] not in self.presented for c in choices):
                raise Blocked('unpresented_baseline_relation')
            return flag,choices
        self.ns['construct_relation_prune_prompt']=prompt;self.ns['clean_relations']=validated


def run(record,graph,model,upstream,seconds=600,on_event=None):
    # Reuse preserved runner with an explicit adapter factory; never modify the
    # parent module or monkeypatch shared global classes during a live run.
    return parent.run(record,graph,model,upstream,seconds,on_event,
                      adapter_factory=CompactAdapter,project_native=True)
