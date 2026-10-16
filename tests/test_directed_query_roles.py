import unittest
from types import SimpleNamespace
from unittest.mock import patch
from flagship_controller.study_runtime import directed_query_roles
from flagship_controller.study_runtime import StudyModel


class DirectedQueryRolesTests(unittest.TestCase):
    def test_optional_audit_input_is_present_in_actual_provider_payload(self):
        requests=[]
        model=StudyModel('http://fixture','fixture',graph=SimpleNamespace(),directed_audit=True)
        inputs={'program':{'steps':[{'relation':'people.person.parents','direction':'in'}]},
                'anchors':[{'mention':'Example','index':0}]}
        def provider(url,payload,timeout):
            requests.append(payload)
            return {'message':{'content':'{}'},'prompt_eval_count':20,'eval_count':2}
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=provider):
            model.direct('Evaluate EVERY fixture requirement',inputs,{'type':'object'})
        import json
        prompt=json.loads(requests[0]['messages'][0]['content'])
        self.assertEqual(prompt['inputs']['directed_query_roles']['directed_atoms'][0]['subject'],'answer')
        self.assertNotIn('directed_query_roles',inputs)
        self.assertEqual(model.semantic_audit[0]['action'],'DIRECTED_ROLE_AUDIT_INPUT')

    def test_default_preserves_historical_request_and_gate_off_skips_representation(self):
        model=StudyModel('http://fixture','fixture',graph=SimpleNamespace(),policy='semantic-gate-off',directed_audit=True)
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=AssertionError('No gate request')):
            self.assertTrue(model.ask('Audit whether fixture',{})['supported'])
        self.assertFalse(any(e['action']=='DIRECTED_ROLE_AUDIT_INPUT' for e in model.semantic_audit))
        self.assertFalse(StudyModel('http://fixture','fixture',graph=SimpleNamespace()).directed_audit)

    def test_incoming_predicate_has_answer_as_subject(self):
        program={'steps':[{'relation':'people.person.parents','direction':'in'}],'constraints':[]}
        atom=directed_query_roles(program,1)['directed_atoms'][0]
        self.assertEqual(atom,{'subject':'answer','predicate':'people.person.parents','object':'anchor0'})

    def test_outgoing_predicate_has_anchor_as_subject(self):
        program={'steps':[{'relation':'people.person.parents','direction':'out'}],'constraints':[]}
        atom=directed_query_roles(program,1)['directed_atoms'][0]
        self.assertEqual(atom,{'subject':'anchor0','predicate':'people.person.parents','object':'answer'})

    def test_mediated_constraint_preserves_actual_predicate_orientation(self):
        program={'steps':[{'relation':'film.actor.film','direction':'out'},
                          {'relation':'film.performance.character','direction':'out'}],
                 'constraints':[{'at':1,'relation':'film.performance.film','direction':'out','anchor':1}]}
        result=directed_query_roles(program,2)
        self.assertEqual(result['directed_atoms'][1]['object'],'answer')
        self.assertEqual(result['directed_atoms'][2],{'subject':'intermediate1',
            'predicate':'film.performance.film','object':'anchor1'})
        program['constraints'][0]['direction']='in'
        self.assertEqual(directed_query_roles(program,2)['directed_atoms'][2]['subject'],'anchor1')
