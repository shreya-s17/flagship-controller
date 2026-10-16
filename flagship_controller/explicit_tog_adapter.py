"""V4 local adaptation: a declared final-answer channel, never prose extraction.

Native reasoning is prompted to declare exact observed names on one final line.
Only that channel is mapped to observed IDs; context mentions cannot be selected.
This changes the baseline prompt/answer contract and does not prove semantics.
"""
import json
from . import tog_adapter as parent
from .indexed_tog_adapter import IndexedAdapter

VERSION='tog-explicit-final-v4'
MARKER='FINAL_ANSWER:'
CHANNEL_INSTRUCTION='''

Output contract for this local adaptation: keep the required initial {Yes} or
{No} control field. If {Yes}, finish with exactly one final line of the form
FINAL_ANSWER: ["exact observed answer name", "another exact observed answer name"]
Use a JSON array of strings, containing ALL AND ONLY your concluded answers to
the question. Copy complete names exactly from the observed triplets, including
earlier triplets if needed. Do not put contextual examples, historical alternatives
or names merely quoted in the question in this array. If {No}, omit this line.
Do not add text after the final line. This declaration is not semantic proof.
'''


def decode(native,names,stop):
    if stop!='reasoning_yes':return [],'native_not_graph_reasoning_yes',None
    lines=native.splitlines()
    declared=[i for i,line in enumerate(lines) if line.strip().startswith(MARKER)]
    nonempty=[i for i,line in enumerate(lines) if line.strip()]
    if len(declared)!=1 or not nonempty or declared[0]!=nonempty[-1]:
        return [],'missing_or_ambiguous_final_answer_channel',None
    line=lines[declared[0]].strip()
    try:labels=json.loads(line[len(MARKER):].strip())
    except json.JSONDecodeError:return [],'invalid_final_answer_json',None
    if not isinstance(labels,list) or len(labels)>100 or any(not isinstance(x,str) or not x.strip() or len(x)>300 for x in labels):
        return [],'invalid_final_answer_labels',None
    if not labels:return [],'explicit_empty_answer',{'labels':[]}
    index={}
    for entity,observed in names.items():
        for name in observed:index.setdefault(name.casefold().strip(),set()).add(entity)
    ids=[];seen=set()
    for label in labels:
        key=label.casefold().strip()
        if key in seen:return [],'duplicate_final_answer_label',None
        seen.add(key);matches=index.get(key,set())
        if len(matches)!=1:return [],'unobserved_or_ambiguous_final_answer',None
        ids.append(next(iter(matches)))
    return list(dict.fromkeys(ids)),'exact_declared_name_mapping_not_semantic_certification',{'labels':labels,'line':line}


class ExplicitAdapter(IndexedAdapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        reasoning=self.ns['reasoning'];request=self.ns['run_llm']
        self.channel_stage=False;self.native_stop=None
        def guarded_reasoning(*args):
            self.channel_stage=True
            try:return reasoning(*args)
            finally:self.channel_stage=False
        def channel_request(text,*args):
            if self.channel_stage:
                self.log('DECLARED_ANSWER_CHANNEL_PROMPT',instruction=CHANNEL_INSTRUCTION,
                    limitation='Additional native prompting; declaration is not semantic certification')
                text+=CHANNEL_INSTRUCTION
            return request(text,*args)
        self.ns['reasoning']=guarded_reasoning;self.ns['run_llm']=channel_request

    def search(self,*args):
        native,chains,stop=super().search(*args);self.native_stop=stop
        return native,chains,stop

    def project_answer(self,question,native,candidates):
        # Use every retrieved observed name, including an earlier beam/anchor.
        # Restricting to the final beam caused a real inverse-answer omission.
        answers,status,channel=decode(native,self.names,self.native_stop)
        self.log('DECLARED_ANSWER_MAPPING',channel=channel,answers=answers,status=status,
            name_scope='all observed graph names; no first/fuzzy match',model_call_skipped=True)
        return answers,status


def run(record,graph,model,upstream,seconds=600,on_event=None):
    return parent.run(record,graph,model,upstream,seconds,on_event,
        adapter_factory=ExplicitAdapter,project_native=True,runtime_version=VERSION)
