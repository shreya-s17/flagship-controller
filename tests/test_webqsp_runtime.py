import json
import unittest
from unittest.mock import patch
from flagship_controller.webqsp_runtime import Freebase, Ollama, Blocked, run_question, identifier
from flagship_controller.webqsp_score import metrics, score

class Model:
    def __init__(self, reject=False): self.calls=self.tokens=0; self.audit=[]; self.reject=reject
    def ask(self, instruction, inputs):
        self.calls+=1; self.tokens+=10; self.audit.append(inputs)
        if self.calls==1: return {'mention':'Example','supported':True}
        if self.calls==2: return {'steps':[{'relation':'r','direction':'out'}],'supported':True}
        return {'supported':not self.reject}

class Graph:
    def __init__(self, ambiguous=False): self.calls=0; self.audit=[]; self.ambiguous=ambiguous
    def link(self,m): self.calls+=1; return ['m.seed','m.other'] if self.ambiguous else ['m.seed']
    def relations(self,n): self.calls+=1; return [{'relation':'r','direction':'out'}]
    def expand(self,n,a):
        self.calls+=1
        return [{'id':x,'source':n,'target':x,'target_key':'uri:'+x,'term':{'type':'uri'},
                 'provenance':{'snapshot':'fixture'}} for x in ['m.a','m.b']]

class RuntimeTests(unittest.TestCase):
    record={'id':'q','question':'Who is related to Example?','split':'pilot'}
    def test_multianswer_and_gate(self):
        r=run_question(self.record,Graph(),Model())
        self.assertEqual(r['answers'],['m.a','m.b']); self.assertEqual(r['terminal'],'ANSWER')
        self.assertEqual(r['cost']['model_tokens'],30)
        self.assertEqual(run_question(self.record,Graph(),Model(True))['terminal'],'ABSTAIN')
    def test_ambiguity_is_not_first_match(self):
        r=run_question(self.record,Graph(True),Model())
        self.assertEqual(r['reason'],'ambiguous_entity'); self.assertFalse(r['answers'])
    def test_gold_boundary(self):
        with self.assertRaises(ValueError): run_question({**self.record,'parses':[]},Graph(),Model())
    def test_faults_do_not_become_empty_evidence(self):
        g=Graph(); g.expand=lambda *args: (_ for _ in ()).throw(OSError('endpoint'))
        self.assertEqual(run_question(self.record,g,Model())['reason'],'runtime_error:OSError')
    def test_identifier_injection_rejected(self):
        with self.assertRaises(Blocked): identifier('m.x } UNION { ?s ?p ?o')
    def test_graph_limit_inverse_and_literals(self):
        g=Freebase('http://fixture','snapshot',row_limit=1)
        g.select=lambda body:[{'target':{'type':'literal','value':'2000','datatype':'date'}}]
        edge=g.expand('m.seed',{'relation':'r','direction':'in'})[0]
        self.assertEqual(edge['target'],'2000'); self.assertEqual(edge['direction'],'in')
        self.assertEqual(edge['term']['datatype'],'date')
    def test_model_accounting_and_cap(self):
        response={'message':{'content':'{"supported":true}'},'prompt_eval_count':8,'eval_count':4}
        m=Ollama('http://fixture','fixture',max_tokens=10)
        with patch('flagship_controller.webqsp_runtime.post_json',return_value=response):
            with self.assertRaisesRegex(Blocked,'exceeded_after_call'): m.ask('i',{})
        self.assertEqual(m.tokens,12)
    def test_sparql_transport_truncation_and_direction(self):
        import io
        g=Freebase('http://fixture','snapshot',row_limit=1)
        payload={'results':{'bindings':[{},{}]}}
        with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(payload).encode())) as send:
            with self.assertRaisesRegex(Blocked,'truncated'): g.select('SELECT ?x WHERE {?x ?p ?o}')
            req=send.call_args.args[0]
            self.assertIn('query=',req.data.decode())
            self.assertEqual(g.calls,1)
        g=Freebase('http://fixture','snapshot')
        payload={'results':{'bindings':[{'target':{'type':'uri','value':'http://rdf.freebase.com/ns/m.a'}}]}}
        with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(payload).encode())) as send:
            g.expand('m.seed',{'relation':'r','direction':'in'})
            from urllib.parse import parse_qs
            self.assertIn('?target ns:r ns:m.seed',parse_qs(send.call_args.args[0].data.decode())['query'][0])
    def test_no_partial_answer_on_witness_cap(self):
        r=run_question(self.record,Graph(),Model(),max_frontier=1)
        self.assertEqual(r['terminal'],'ABSTAIN'); self.assertEqual(r['answers'],[])
    def test_unreported_usage_and_malformed_json(self):
        m=Ollama('http://fixture','fixture')
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={}):
            with self.assertRaisesRegex(Blocked,'usage_unavailable'): m.ask('i',{})
        m=Ollama('http://fixture','fixture')
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={
             'prompt_eval_count':1,'eval_count':1,'message':{'content':'bad'}}):
            with self.assertRaisesRegex(Blocked,'invalid_model_json'): m.ask('i',{})
    def test_metrics_and_exclusions(self):
        self.assertAlmostEqual(metrics(['a'],['a','b'])['f1'],2/3)
        pred=[{'id':'q','terminal':'ANSWER','answers':['a']}]
        self.assertIsNone(score(pred,[{'id':'q','parses':[]}])['macro_f1'])
        gold=[{'id':'q','parses':[{'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},
                                     'Answers':[{'AnswerArgument':'a'}]}]}]
        self.assertEqual(score(pred,gold)['em'],1)

if __name__=='__main__': unittest.main()
