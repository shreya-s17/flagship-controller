import unittest
from unittest.mock import patch
from flagship_controller.semantic_runtime import validate_contract,permitted_programs,requirement_gate,SemanticGraph,SemanticModel
from flagship_controller.webqsp_runtime import Blocked


def contract():
    return {'supported':True,'anchors':[{'mention':'Atlas','type_hint':'organization'}],'answer_category':'business_category',
      'requirements':[{'kind':'answer_type','span':'industries','description':'Business industries, not fictional people'},
                      {'kind':'relation','span':'operate','description':'Industries in which the named company operates'}]}


class SemanticRequirementTests(unittest.TestCase):
    def test_question_grounding_and_required_kinds(self):
        c=contract();self.assertIs(validate_contract('In which industries does Atlas operate?',c),c)
        for span in ['not quoted','all required constraints']:
            c=contract();c['requirements'][0]['span']=span
            with self.assertRaisesRegex(Blocked,'not_in_question'):validate_contract('In which industries does Atlas operate?',c)
        c=contract();c['requirements'][1]['kind']='qualifier'
        with self.assertRaisesRegex(Blocked,'incomplete'):validate_contract('In which industries does Atlas operate?',c)

    def test_known_schema_mismatch_excluded_unknown_is_explicit(self):
        programs=[{'index':0,'answer_expected_type':'business.industry'},
          {'index':1,'answer_expected_type':'fictional_universe.fictional_character'}, {'index':2,'answer_expected_type':None}]
        self.assertEqual([p['index'] for p in permitted_programs(contract(),programs)],[0,2])
        self.assertEqual(len(permitted_programs({**contract(),'answer_category':'unknown'},programs)),3)

    def test_each_requirement_needs_nonempty_valid_evidence(self):
        verdicts=[{'index':i,'status':'satisfied','evidence_steps':[0]} for i in range(2)]
        self.assertTrue(requirement_gate(contract(),{'verdicts':verdicts},1)['supported'])
        for status in ('unknown','contradicted'):
            changed=[dict(v) for v in verdicts];changed[1]['status']=status
            self.assertFalse(requirement_gate(contract(),{'verdicts':changed},1)['supported'])
        changed=[dict(v) for v in verdicts];changed[1]['evidence_steps']=[]
        self.assertFalse(requirement_gate(contract(),{'verdicts':changed},1)['supported'])
        with self.assertRaisesRegex(Blocked,'incomplete'):requirement_gate(contract(),{'verdicts':verdicts[:1]},1)
        with self.assertRaisesRegex(Blocked,'index'):requirement_gate(contract(),{'verdicts':[verdicts[0],verdicts[0]]},1)
        for bad in (True,-1,1):
            changed=[dict(v) for v in verdicts];changed[1]['evidence_steps']=[bad]
            with self.assertRaises(Blocked):requirement_gate(contract(),{'verdicts':changed},1)

    def test_reflexive_answer_rejects_whole_set(self):
        g=SemanticGraph('http://invalid','fixture')
        with patch('flagship_controller.structured_runtime.StructuredGraph.execute',return_value=(['m.topic','m.other'],[])):
            with self.assertRaisesRegex(Blocked,'reflexive'):g.execute(['m.topic'],{})

    def test_valid_answer_cards_do_not_change_answer_set(self):
        g=SemanticGraph('http://invalid','fixture');g.select=lambda q:[{'name':{'value':'Industry'},'type':{'value':'http://rdf.freebase.com/ns/business.industry'}}]
        with patch('flagship_controller.structured_runtime.StructuredGraph.execute',return_value=(['m.industry'],[['witness']])):
            self.assertEqual(g.execute(['m.topic'],{}),(['m.industry'],[['witness']]))
        self.assertEqual(g.answer_cards[0]['observed_types'],['business.industry'])

    def test_provider_cannot_select_disallowed_type_index(self):
        model=SemanticModel('http://invalid','fixture',graph=SemanticGraph('http://invalid','fixture'));model.contract=contract()
        inputs={'programs':[{'index':0,'answer_expected_type':'business.industry'}, {'index':1,'answer_expected_type':'fictional_universe.fictional_character'}]}
        with patch('flagship_controller.structured_runtime.StructuredModel.ask',return_value={'program_index':1}):
            with self.assertRaisesRegex(Blocked,'disallowed'):model.ask('Choose a program',inputs)

class SourceSpanAndLinkTests(unittest.TestCase):
    def test_decoder_span_choices_are_actual_question_substrings(self):
        from flagship_controller.semantic_runtime import question_spans
        question='Which postal codes serve the City of Example?'
        spans=question_spans(question)
        self.assertIn('postal codes',spans)
        self.assertIn('City of Example',spans)
        self.assertTrue(all(span in question for span in spans))
        self.assertNotIn('city of example',spans)

    def test_canonical_key_retains_type_and_case_insensitive_name_guard(self):
        graph=SemanticGraph('http://invalid','snapshot');queries=[]
        def select(query):
            queries.append(query)
            return [{'entity':{'type':'uri','value':'http://rdf.freebase.com/ns/m.person'}}]
        graph.select=select
        ids,method=graph.typed_link('example de person','person')
        self.assertEqual(ids,['m.person'])
        self.assertIn('LCASE(STR(?name))="example de person"',queries[0])
        self.assertIn('ns:people.person',queries[0]);self.assertIn('"/en/example_de_person"',queries[0])
        self.assertIn('casefold',method)

class ContractRetrievalTests(unittest.TestCase):
    def test_symmetric_parent_normalization_and_no_answer_id_dependency(self):
        from flagship_controller.semantic_runtime import contract_rank
        relations=[{'relation':'common.topic.notable_types','direction':'out'},
                   {'relation':'people.person.parents','direction':'out'}]
        requirements=[{'span':'parents','description':'Parents of the named person'}]
        self.assertEqual(contract_rank('Who are Example parents?',requirements,relations,1)[0]['relation'],'people.person.parents')
        self.assertEqual(contract_rank('Who are Different parents?',requirements,relations,1)[0]['relation'],'people.person.parents')

class ObservedTypeRetrievalTests(unittest.TestCase):
    def test_wrong_inferred_hint_is_soft_but_key_and_name_still_required(self):
        graph=SemanticGraph('http://invalid','snapshot');queries=[]
        def select(query):
            queries.append(query)
            if 'type.object.key' in query and 'type.object.type' not in query:
                return [{'entity':{'type':'uri','value':'http://rdf.freebase.com/ns/m.school'}}]
            return []
        graph.select=select
        ids,method=graph.typed_link('Example University','musical')
        self.assertEqual(ids,['m.school']);self.assertIn('fallback',method)
        self.assertEqual(graph.link_repairs[0]['inferred_type_hint'],'musical')
        self.assertIn('LCASE(STR(?name))',queries[-1]);self.assertIn('"/en/example_university"',queries[-1])

    def test_observed_schema_can_rescue_root_outside_lexical_top32(self):
        graph=SemanticGraph('http://invalid','snapshot');graph.question='What category does Example offer?';graph.question_contract=contract()
        relations=[{'relation':'a.namespace.relation'+str(i),'direction':'out'} for i in range(40)]+[{'relation':'z.company.industry','direction':'out'}]
        def select(query):
            if 'type.property.expected_type' in query:
                return [{'relation':{'value':'http://rdf.freebase.com/ns/z.company.industry'},'expected':{'value':'http://rdf.freebase.com/ns/business.industry'}}]
            return []
        graph.select=select
        with patch('flagship_controller.structured_runtime.StructuredGraph.inventory',return_value=relations):
            retrieved=graph.inventory('m.topic')
        self.assertEqual(len(retrieved),32)
        self.assertIn({'relation':'z.company.industry','direction':'out'},retrieved)
        self.assertEqual(len(graph.observed_inventory),41)
        self.assertEqual(graph.root_expected_types['z.company.industry out'],['business.industry'])

class MissingCanonicalKeyTests(unittest.TestCase):
    def test_untyped_name_fallback_when_prepared_graph_has_no_key(self):
        graph=SemanticGraph('http://invalid','snapshot')
        def select(query):
            if 'VALUES ?label' in query and 'type.object.type' not in query and 'type.object.key' not in query and 'type.object.name' in query:
                return [{'entity':{'type':'uri','value':'http://rdf.freebase.com/ns/m.school'}}]
            return []
        graph.select=select
        ids,method=graph.typed_link('Example University','musical')
        self.assertEqual(ids,['m.school']);self.assertIn('type.object.name',method)
        self.assertEqual(graph.link_repairs[0]['inferred_type_hint'],'musical')

class ObservedRootInclusionTests(unittest.TestCase):
    def test_observed_direct_root_cannot_be_lost_by_model_root_choice(self):
        graph=SemanticGraph('http://invalid','snapshot');graph.question='Which industries does Example operate in?'
        graph.root_expected_types={'business.company.industry out':['business.industry']}
        model=SemanticModel('http://invalid','fixture',graph=graph);model.contract=contract()
        correct={'relation':'business.company.industry','direction':'out'}
        unrelated={'relation':'common.topic.image','direction':'out'}
        with patch('flagship_controller.structured_runtime.StructuredModel.ask',return_value={'roots':[unrelated]}):
            result=model.ask('Select up to THREE',{'available':[correct,unrelated]})
        self.assertIn(correct,result['roots']);self.assertLessEqual(len(result['roots']),3)
        self.assertEqual(model.semantic_audit[-1]['included_observed_type_roots'],[correct])
