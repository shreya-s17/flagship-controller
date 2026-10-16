"""V3 local adaptation: indexed relations and actual native-name text spans.

Decoding constraints prevent invented relations/quotes, not semantic mistakes.
No annotations or scorer are available to this runtime. V1/V2 remain preserved.
"""
import math
import re
from . import tog_adapter as parent
from .compact_tog_adapter import CompactAdapter
from .structured_runtime import object_schema, BOOLEAN, rank_relations
from .webqsp_runtime import Blocked

VERSION = 'tog-indexed-spans-v3'


def relation_text(response, names, width):
    selections = response.get('selections')
    if not isinstance(selections, list) or len(selections) > width:
        raise Blocked('invalid_indexed_relation_selection')
    seen = set(); fields = []
    for selection in selections:
        index = selection.get('index'); score = selection.get('score')
        if type(index) is not int or not 0 <= index < len(names) or index in seen:
            raise Blocked('invalid_indexed_relation_index')
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise Blocked('invalid_indexed_relation_score')
        seen.add(index)
        fields.append('{'+names[index]+' (Score: '+str(float(score))+')}')
    return '\n'.join(fields)


def native_spans(native, candidates):
    """Return exact observed-name occurrences; omit aliases shared across IDs.

    Casefolding is never used for offsets (it can change Unicode string length).
    A span is evidence of mention only, not that the name is a concluded answer.
    """
    occurrences = {}
    for candidate in candidates:
        for name in candidate['names']:
            if not isinstance(name, str) or not name.strip(): continue
            for match in re.finditer(r'(?<!\w)'+re.escape(name)+r'(?!\w)', native, re.IGNORECASE):
                key = (match.start(), match.end())
                occurrences.setdefault(key, set()).add(candidate['entity'])
    spans = []
    for (start, end), entities in sorted(occurrences.items()):
        if len(entities) != 1: continue
        # Different IDs with overlapping names cannot be uniquely normalized.
        if any(a < end and b > start and other != entities
               for (a,b),other in occurrences.items()): continue
        spans.append({'entity': next(iter(entities)), 'start': start, 'end': end,
            'quote': native[start:end], 'context': native[max(0,start-140):min(len(native),end+140)]})
    return spans


def validate_spans(response, spans, native):
    if response.get('supported') is not True: return [], 'native_answer_not_explicit'
    if response.get('all_concluded_answers_represented') is not True:
        return [], 'native_answer_not_fully_represented'
    selections = response.get('span_indices')
    if not isinstance(selections,list) or not selections: return [], 'missing_native_span_selection'
    seen = set(); answers = []
    for index in selections:
        if type(index) is not int or not 0 <= index < len(spans) or index in seen:
            raise Blocked('invalid_native_span_index')
        span = spans[index]; seen.add(index)
        if native[span['start']:span['end']] != span['quote']:
            raise Blocked('native_span_source_mismatch')
        answers.append(span['entity'])
    return list(dict.fromkeys(answers)), 'charged_model_span_selection; not semantic proof'


class IndexedAdapter(CompactAdapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        original_prompt = self.ns['construct_relation_prune_prompt']
        raw = self.ns['run_llm']; self.pending_relation = None
        def prompt(question, entity, relations, settings):
            text = original_prompt(question, entity, relations, settings)
            # The parent's lexical ordering is also the ordering in its prompt.
            names = [r['relation'] for r in rank_relations(question,
                [{'relation':r,'direction':'out'} for r in dict.fromkeys(relations)],[],limit=32)]
            self.pending_relation = (text, question, entity, names, settings.width)
            return text
        def request(text,*args):
            pending = self.pending_relation
            if pending is None: return raw(text,*args)
            self.pending_relation = None
            expected, question, entity, names, width = pending
            if text != expected: raise Blocked('indexed_relation_stage_mismatch')
            if not names:
                self.log('INDEXED_RELATION_SELECTION',candidates=[],selection={'selections':[]},model_call_skipped=True)
                return ''
            self.checkpoint()
            schema = object_schema({'selections':{'type':'array','maxItems':width,
                'items':object_schema({'index':{'type':'integer','enum':list(range(len(names)))},
                    'score':{'type':'number','minimum':0,'maximum':1}})}})
            response = self.model.direct('Choose up to the requested width of supplied relation indices relevant to answering the question from the topic entity. Assign relevance scores between 0 and 1. Select only supplied indices, without duplicates. Empty selections are permitted when none is relevant. These scores are search weights, not calibrated probabilities.',
                {'question':question,'topic_entity':entity,'width':width,
                 'relations':[{'index':i,'relation':name} for i,name in enumerate(names)]},schema)
            self.log('INDEXED_RELATION_SELECTION',candidates=names,selection=response,
                original_prompt=expected,adaptation='structured indexed relation prompt replaces upstream free-text relation request')
            return relation_text(response,names,width)
        self.ns['construct_relation_prune_prompt'] = prompt
        self.ns['run_llm'] = request

    def project_answer(self,question,native,candidates):
        spans = native_spans(native,candidates)
        if len(spans) > 64:
            self.log('NATIVE_SPAN_EXTRACTION',candidates=candidates,span_count=len(spans),model_call_skipped=True)
            return [], 'native_span_presentation_cap'
        if not spans:
            self.log('NATIVE_SPAN_EXTRACTION',candidates=candidates,spans=[],model_call_skipped=True)
            return [], 'no_unambiguous_native_name_spans'
        self.checkpoint()
        schema = object_schema({'supported':BOOLEAN,'all_concluded_answers_represented':BOOLEAN,
            'span_indices':{'type':'array','maxItems':len(spans),
                'items':{'type':'integer','enum':list(range(len(spans)))}}})
        selection = self.model.direct('Extract only explicit final answers concluded in the native response, using the supplied text span indices. Mentioning a name as context, a rejected alternative, a partial clue, or a speculative inference is insufficient. Select all concluded answer entities only if all are represented by supplied spans. Do not answer the question again or add facts. Otherwise supported false and empty span_indices. all_concluded_answers_represented must be false if any concluded answer has no supplied span. This is extraction, not semantic certification.',
            {'question':question,'native_response':native,'spans':spans},schema)
        self.log('NATIVE_SPAN_EXTRACTION',candidates=candidates,spans=spans,selection=selection)
        return validate_spans(selection,spans,native)


def run(record,graph,model,upstream,seconds=600,on_event=None):
    return parent.run(record,graph,model,upstream,seconds,on_event,
        adapter_factory=IndexedAdapter,project_native=True,runtime_version=VERSION)
