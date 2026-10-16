import unittest
from flagship_controller.structured_runtime import compile_program, validate_question, run, Blocked

class StructuredTests(unittest.TestCase):
    def test_constraint_join_and_inverse(self):
        program={'steps':[{'relation':'film.actor.film','direction':'out'},{'relation':'film.performance.character','direction':'out'}],
                 'constraints':[{'at':1,'relation':'film.performance.film','direction':'out','anchor':1}]}
        query,triples=compile_program(['m.person','m.film'],program)
        self.assertIn('?v1 ns:film.performance.film ns:m.film',query)
        self.assertIn('?v1 ns:film.performance.character ?v2',query)
        self.assertIn('LIMIT 101',query)
        program['steps'][0]['direction']='in'
        self.assertIn('?v1 ns:film.actor.film ?v0',compile_program(['m.person','m.film'],program)[0])
    def test_canonical_key_is_type_and_name_guarded(self):
        from flagship_controller.structured_runtime import StructuredGraph
        g=StructuredGraph('http://fixture','snapshot');queries=[]
        def select(query):
            queries.append(query)
            return [{'entity':{'type':'uri','value':'http://rdf.freebase.com/ns/m.example'}}]
        g.select=select
        nodes,method=g.typed_link('the Example','city')
        self.assertEqual(nodes,['m.example'])
        self.assertIn('"/en/example"',queries[0]);self.assertIn('ns:location.citytown',queries[0])
        self.assertIn('ns:type.object.name ?label',queries[0]);self.assertEqual(method,'type.object.key+name+type')
    def test_constrained_roots_cannot_invent_candidate(self):
        from flagship_controller.structured_runtime import StructuredModel
        from unittest.mock import patch
        choices=[{'relation':'observed','direction':'out'}]
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={'prompt_eval_count':1,'eval_count':1,'message':{'content':'{"roots":[]}'}}) as send:
            StructuredModel('http://fixture','fixture').ask('Select up to three',{'available':choices})
        self.assertEqual(send.call_args.args[1]['format']['properties']['root_indices']['items']['enum'],[0])
    def test_complete_inventory_pagination_rejects_exhaustion(self):
        from flagship_controller.structured_runtime import StructuredGraph
        g=StructuredGraph('http://fixture','snapshot',row_limit=2)
        g.select=lambda query:[{},{}]
        with self.assertRaisesRegex(Blocked,'inventory_page_cap'):g.paged('SELECT ?x WHERE {}','?x',max_pages=2)
    def test_failure_triggered_join_hints_come_from_graph(self):
        from flagship_controller.structured_runtime import StructuredGraph
        graph=StructuredGraph('http://fixture','snapshot');seen=[]
        def select(query):
            seen.append(query)
            return [{'at':{'value':'1'},'relation':{'value':'http://rdf.freebase.com/ns/film.performance.film'},'direction':{'value':'out'}}]
        graph.select=select
        program={'steps':[{'relation':'film.actor.film','direction':'out'},{'relation':'film.performance.character','direction':'out'}],
                 'constraints':[{'at':0,'relation':'film.performance.actor','direction':'in','anchor':1}]}
        hints=graph.join_hints(['m.actor','m.film'],program)
        self.assertEqual(hints,[{'at':1,'relation':'film.performance.film','direction':'out','anchor':1}])
        self.assertIn('ns:m.film',seen[0]);self.assertIn('LIMIT 101',seen[0])
    def test_single_anchor_decoder_forbids_extra_constraints(self):
        from flagship_controller.structured_runtime import StructuredModel
        from unittest.mock import patch
        inputs={'roots':[{'relation':'r','direction':'out'}],'schema':[],'anchors':[{'index':0}]}
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={'prompt_eval_count':1,'eval_count':1,'message':{'content':'{}'}}) as send:
            StructuredModel('http://fixture','fixture').ask('Return JSON plan',inputs)
        self.assertEqual(send.call_args.args[1]['format']['properties']['constraints']['maxItems'],0)
    def test_catalog_requires_observed_secondary_anchor_join(self):
        from flagship_controller.structured_runtime import program_catalog
        root={'relation':'film.actor.film','direction':'out'}
        schema=[{'root':'film.actor.film','expected':'film.performance','relation':'film.performance.character','child_expected':'fictional_universe.fictional_character'}]
        self.assertEqual(program_catalog([root],schema,2,{}),[])
        programs=program_catalog([root],schema,2,{'1':[{'r1':'film.actor.film','r2':'film.performance.film'}]})
        self.assertEqual(len(programs),2)
        self.assertEqual(programs[1]['program']['constraints'],[{'at':1,'relation':'film.performance.film','direction':'out','anchor':1}])
        self.assertEqual(programs[1]['answer_expected_type'],'fictional_universe.fictional_character')
        for row in programs:self.assertTrue(all(a['direction']=='out' for a in row['program']['steps']))
    def test_context_overflow_cannot_produce_a_plan(self):
        from flagship_controller.structured_runtime import StructuredModel
        from unittest.mock import patch
        model=StructuredModel('http://fixture','fixture')
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={'prompt_eval_count':3100,'eval_count':1,'message':{'content':'{"supported":true}'}}):
            with self.assertRaisesRegex(Blocked,'context_budget_exceeded'):model.ask('Extract all anchors',{'question':'Example?'})
        self.assertEqual(model.tokens,3101)
    def test_missing_constraint_and_injection_rejected(self):
        program={'steps':[{'relation':'r','direction':'out'}],'constraints':[]}
        with self.assertRaisesRegex(Blocked,'unbound'):compile_program(['m.a','m.b'],program)
        program['steps'][0]['relation']='r } UNION {?s ?p ?o'
        with self.assertRaises(Blocked):compile_program(['m.a'],program)
    def test_constraint_index_and_boolean_rejected(self):
        for at in [True,-1,2,'1']:
            program={'steps':[{'relation':'r','direction':'out'}],'constraints':[{'at':at,'relation':'r','direction':'in','anchor':1}]}
            with self.assertRaises(Blocked):compile_program(['m.a','m.b'],program)
    def test_gold_boundary_and_unsupported_operations(self):
        with self.assertRaises(ValueError):validate_question({'id':'q','question':'Where?','parses':[]})
        for q in ['What are the three major rivers in Asia?','Who was killed first A or B?','How many countries border X?']:
            with self.assertRaisesRegex(Blocked,'unsupported_operator'):validate_question({'id':'q','question':q})
        validate_question({'id':'q','question':'What films did Actor appear in?'})
    def test_repair_can_recover_and_fixed_cannot(self):
        class Graph:
            calls=0;row_limit=100
            def __init__(self):self.audit=[]
            def typed_link(self,*args):self.calls+=1;return ['m.person'],'type.object.name'
            def inventory(self,*args):self.calls+=1;return [{'relation':'bad','direction':'out'},{'relation':'good','direction':'out'}]
            def schema(self,*args):self.calls+=1;return []
            def execute(self,anchors,program):
                self.calls+=1
                return (['m.answer'],[[{'provenance':{'snapshot':'fixture'}}]]) if program['steps'][0]['relation']=='good' else ([],[])
        class Model:
            def __init__(self):self.calls=self.tokens=self.plans=0;self.audit=[]
            def ask(self,instruction,inputs):
                self.calls+=1;self.tokens+=1
                if 'Extract all' in instruction:return {'supported':True,'anchors':[{'mention':'Example','type_hint':'person'}],'obligations':['relation requested']}
                if 'Select up to' in instruction:return {'roots':[{'relation':'bad','direction':'out'},{'relation':'good','direction':'out'}]}
                if instruction.startswith('Choose a program'):
                    self.plans+=1;return {'program_index':0 if self.plans==1 else 1}
                return {'supported':True,'missing_obligations':[]}
        record={'id':'q','question':'Who is related to Example?','split':'pilot'}
        a=run(record,Graph(),Model(),'repair');b=run(record,Graph(),Model(),'fixed')
        self.assertEqual(a['terminal'],'ANSWER');self.assertEqual(b['terminal'],'ABSTAIN')
        self.assertEqual(sum(t['action']=='REPAIR_PLAN' for t in a['trace']),1)
    def test_semantic_rejection_never_emits_answer(self):
        # Invalid grammar must fail before any endpoint execution.
        for payload in [None,{'steps':[]},{'steps':[{'relation':'r','direction':'sideways'}]}, {'steps':[{'relation':'r','direction':'out'}],'query':'SELECT secret'}]:
            with self.assertRaises(Blocked):compile_program(['m.a'],payload)

if __name__=='__main__':unittest.main()
