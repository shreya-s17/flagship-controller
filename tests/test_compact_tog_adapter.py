import unittest
from unittest.mock import patch
from types import SimpleNamespace
from flagship_controller.compact_tog_adapter import validate_projection
from flagship_controller.webqsp_runtime import Blocked


class ProjectionTests(unittest.TestCase):
    candidates=[{'entity':'m.a','names':['Mexico']},{'entity':'m.b','names':['US']}]
    def test_explicit_name_quote_can_map_an_unbraced_conclusion(self):
        native='The answer is Mexico.'
        response={'supported':True,'selections':[{'index':0,'quote':'answer is Mexico'}]}
        self.assertEqual(validate_projection(response,self.candidates,native)[0],['m.a'])

    def test_invented_quote_cannot_rescue_a_candidate(self):
        with self.assertRaisesRegex(Blocked,'not_in_response'):
            validate_projection({'supported':True,'selections':[{'index':0,'quote':'Mexico'}]},self.candidates,'Not provided')

    def test_exact_word_boundaries_and_selected_name_are_required(self):
        with self.assertRaisesRegex(Blocked,'name_not'):
            validate_projection({'supported':True,'selections':[{'index':1,'quote':'RUSSIA'}]},self.candidates,'RUSSIA')
        with self.assertRaisesRegex(Blocked,'name_not'):
            validate_projection({'supported':True,'selections':[{'index':1,'quote':'Mexico'}]},self.candidates,'Mexico')

    def test_unobserved_duplicate_and_boolean_indices_cannot_answer(self):
        for indices in ([2],[True],[0,0]):
            response={'supported':True,'selections':[{'index':i,'quote':'Mexico'} for i in indices]}
            with self.assertRaisesRegex(Blocked,'index'):validate_projection(response,self.candidates,'Mexico')

    def test_unsupported_and_empty_extraction_abstain(self):
        for response in ({'supported':False,'selections':[{'index':0,'quote':'Mexico'}]}, {'supported':True,'selections':[]}):
            self.assertEqual(validate_projection(response,self.candidates,'Mexico')[0],[])


class PresentationTests(unittest.TestCase):
    def adapter(self):
        from flagship_controller.compact_tog_adapter import CompactAdapter
        functions={'construct_relation_prune_prompt':lambda q,e,rels,args:rels,
            'clean_relations':lambda text,node,heads:(True,[{'relation':text,'entity':node,'head':True}])}
        with patch('flagship_controller.tog_adapter.load_upstream',return_value=functions):
            return CompactAdapter(None,None,SimpleNamespace(model='fixture'),lambda *a,**kw:None,lambda:None)

    def test_context_cap_is_deterministic_and_can_retain_late_lexical_match(self):
        adapter=self.adapter()
        relations=['a.unrelated.'+str(i) for i in range(50)]+['z.currency.used']
        prompt=adapter.ns['construct_relation_prune_prompt']('Which currency is used?','Topic',relations,None)
        self.assertEqual(len(prompt),32);self.assertIn('z.currency.used',prompt)
        self.assertEqual(prompt,adapter.ns['construct_relation_prune_prompt']('Which currency is used?','Topic',list(reversed(relations)),None))

    def test_model_cannot_pick_an_observed_but_unpresented_relation(self):
        adapter=self.adapter()
        adapter.ns['construct_relation_prune_prompt']('Currency?','Topic',['currency.used'],None)
        with self.assertRaisesRegex(Blocked,'unpresented'):
            adapter.ns['clean_relations']('other.observed','m.topic',['currency.used','other.observed'])

if __name__=='__main__':unittest.main()
