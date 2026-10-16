import unittest
from types import SimpleNamespace
from unittest.mock import patch
from flagship_controller.indexed_tog_adapter import (
    IndexedAdapter, native_spans, relation_text, validate_spans)
from flagship_controller.webqsp_runtime import Blocked


class IndexedRelationTests(unittest.TestCase):
    def test_indices_map_only_to_presented_relations_and_keep_scores(self):
        self.assertEqual(relation_text({'selections':[{'index':1,'score':.75}]},['r.a','r.b'],3),
            '{r.b (Score: 0.75)}')
        self.assertEqual(relation_text({'selections':[]},[],3),'')

    def test_bad_indices_scores_duplicates_and_width_fail_closed(self):
        for selection in ([{'index':True,'score':1}], [{'index':2,'score':1}],
                          [{'index':0,'score':1}]*2, [{'index':0,'score':float('nan')}],
                          [{'index':0,'score':True}], [{'index':0,'score':-1}]):
            with self.assertRaises(Blocked): relation_text({'selections':selection},['r.a'],3)
        with self.assertRaises(Blocked): relation_text({'selections':[{'index':0,'score':1}]},['r.a'],0)

    def test_small_score_uses_upstream_decimal_syntax_without_losing_weight(self):
        import re
        text=relation_text({'selections':[{'index':0,'score':1e-12}]},['r.a'],3)
        match=re.fullmatch(r'\{r\.a \(Score: ([0-9.]+)\)\}',text)
        self.assertIsNotNone(match)
        self.assertEqual(float(match[1]),1e-12)

    def adapter(self,response):
        events=[]; calls=[]
        def direct(instruction,inputs,schema):
            calls.append((instruction,inputs,schema)); return response
        functions={'construct_relation_prune_prompt':lambda q,e,rels,args:';'.join(rels),
            'clean_relations':lambda text,node,heads:(True,[{'relation':text}])}
        with patch('flagship_controller.tog_adapter.load_upstream',return_value=functions):
            adapter=IndexedAdapter(None,None,SimpleNamespace(model='fixture',direct=direct),
                lambda action,**kw:events.append({'action':action,**kw}),lambda:None)
        return adapter,calls,events

    def test_only_relation_stage_uses_charged_structured_request(self):
        adapter,calls,events=self.adapter({'selections':[{'index':0,'score':1}]})
        text=adapter.ns['construct_relation_prune_prompt']('Which currency?','Topic',['currency.used'],SimpleNamespace(width=3))
        self.assertEqual(adapter.ns['run_llm'](text),'{currency.used (Score: 1.0)}')
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][2]['properties']['selections']['items']['properties']['index']['enum'],[0])
        self.assertIsNone(adapter.pending_relation)
        self.assertEqual(events[-1]['action'],'INDEXED_RELATION_SELECTION')

    def test_empty_relations_skip_request_and_stage_mismatch_is_rejected(self):
        adapter,calls,_=self.adapter({'selections':[]})
        text=adapter.ns['construct_relation_prune_prompt']('Q','Topic',[],SimpleNamespace(width=3))
        self.assertEqual(adapter.ns['run_llm'](text),''); self.assertEqual(calls,[])
        adapter.ns['construct_relation_prune_prompt']('Q','Topic',['r.a'],SimpleNamespace(width=3))
        with self.assertRaisesRegex(Blocked,'stage_mismatch'):adapter.ns['run_llm']('wrong stage')


class NativeSpanTests(unittest.TestCase):
    candidates=[{'entity':'m.mx','names':['Mexico']},{'entity':'m.us','names':['US']}]
    def response(self,indices):
        return {'supported':True,'all_concluded_answers_represented':True,'span_indices':indices}

    def test_inverse_unquoted_native_answer_projects_without_generating_quote(self):
        native='The Mexican peso is used in Mexico. The answer is {Mexico}.'
        spans=native_spans(native,self.candidates)
        self.assertEqual([s['quote'] for s in spans],['Mexico','Mexico'])
        self.assertEqual(validate_spans(self.response([1]),spans,native)[0],['m.mx'])

    def test_shared_aliases_and_substrings_cannot_create_a_unique_candidate(self):
        self.assertEqual(native_spans('RUSSIA and Mexican.',self.candidates),[])
        self.assertEqual(native_spans('Mexico',[*self.candidates,{'entity':'m.other','names':['Mexico']}]),[])

    def test_overlapping_names_for_different_entities_are_ambiguous(self):
        self.assertEqual(native_spans('University Yale',[
            {'entity':'m.a','names':['University Yale']},
            {'entity':'m.b','names':['Yale']}]),[])

    def test_unicode_offsets_reference_original_native_text(self):
        native='İstanbul: MEXICO.'
        spans=native_spans(native,self.candidates)
        self.assertEqual(spans[0]['quote'],'MEXICO')
        self.assertEqual(native[spans[0]['start']:spans[0]['end']],'MEXICO')

    def test_unknown_out_of_range_boolean_and_duplicate_span_indices_fail(self):
        native='Mexico';spans=native_spans(native,self.candidates)
        for indices in ([True],[1],[-1],[0,0]):
            with self.assertRaisesRegex(Blocked,'span_index'):validate_spans(self.response(indices),spans,native)

    def test_missing_completeness_or_support_cannot_drop_unmapped_conclusions(self):
        native='Mexico and an unobserved country';spans=native_spans(native,self.candidates)
        for field in ('supported','all_concluded_answers_represented'):
            response=self.response([0]);response[field]=False
            self.assertEqual(validate_spans(response,spans,native)[0],[])

    def test_changed_source_cannot_supply_a_quote(self):
        spans=native_spans('Mexico',self.candidates)
        with self.assertRaisesRegex(Blocked,'source_mismatch'):validate_spans(self.response([0]),spans,'Other')

    def test_projection_skips_model_when_no_actual_name_span_exists(self):
        adapter,calls,events=IndexedRelationTests().adapter({})
        answers,status=adapter.project_answer('Q','Not enough evidence',self.candidates)
        self.assertEqual(answers,[]);self.assertEqual(calls,[])
        self.assertEqual(status,'no_unambiguous_native_name_spans')

if __name__=='__main__': unittest.main()
