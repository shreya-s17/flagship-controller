import copy
import unittest
from flagship_controller.witness_audit import audit

class WitnessAuditTests(unittest.TestCase):
    def fixture(self):
        ns='http://rdf.freebase.com/ns/'
        term=lambda name:{'type':'uri','value':ns+name}
        return {'id':'fixture','terminal':'ANSWER','answers':['m.answer'],
            'trace':[{'action':'LINK','candidates':['m.seed']},{'action':'PLAN','program':{'steps':[{'relation':'r','direction':'out'}],'constraints':[]}}],
            'witnesses':[[{'source':term('m.seed'),'relation':'r','target':term('m.answer'),'provenance':{'query_index':0,'snapshot':'fixture'}}]],
            'graph_audit':[{'rows':[{'v1':term('m.answer')}],'snapshot':'fixture','sql_state':'00000'}]}
    def test_witness_rows_and_answers_are_consistent(self):
        r=audit(self.fixture());self.assertTrue(r['recorded_row_consistency']);self.assertEqual(r['semantic_validity'],'not assessed')
    def test_tampered_predicate_row_snapshot_answer_rejected(self):
        for kind in ('predicate','row','snapshot','answer','partial'):
            r=self.fixture()
            if kind=='predicate':r['witnesses'][0][0]['relation']='fabricated'
            if kind=='row':r['graph_audit'][0]['rows'][0]['v1']['value']='wrong'
            if kind=='snapshot':r['witnesses'][0][0]['provenance']['snapshot']='different'
            if kind=='answer':r['answers']=['not_witnessed']
            if kind=='partial':r['graph_audit'][0]['sql_state']='S1TAT'
            with self.assertRaises(ValueError):audit(r)
    def test_abstention_never_counts_as_supported_answer(self):
        r=self.fixture();r.update(terminal='ABSTAIN',answers=[]);self.assertFalse(audit(r)['answered'])
        r['answers']=['bad']
        with self.assertRaises(ValueError):audit(r)
