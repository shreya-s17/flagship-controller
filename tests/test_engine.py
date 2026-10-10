import copy
import unittest
from flagship_controller.engine import Config, LocalEvidence, execute, check
from flagship_controller.evaluate import proofs, ratio, score
from flagship_controller.synthetic import suite


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.records = suite(5)

    def test_all_answered_witnesses_pass_independent_oracle(self):
        for record in self.records:
            result = execute(record['query'], LocalEvidence(record['graph']))
            if result['terminal'] == 'ANSWER':
                self.assertIn((result['answer'],result['proof']), proofs(record['query'],record['graph']))

    def test_deleted_edge_with_alternative_is_supported(self):
        record = next(r for r in self.records if r['condition']=='support_deletion')
        self.assertTrue(proofs(record['query'], record['graph']))

    def test_conflict_uses_actual_denial_not_gold_label(self):
        record = next(r for r in self.records if r['condition']=='conflict')
        self.assertFalse(proofs(record['query'], record['graph']))
        result = execute(record['query'], LocalEvidence(record['graph']))
        self.assertEqual(result['terminal'],'ABSTAIN')

    def test_gold_and_condition_never_change_controller(self):
        record = self.records[0]
        result = execute(record['query'],LocalEvidence(record['graph']))
        changed = copy.deepcopy(record); changed['factual_answers']=['fake']; changed['condition']='fake'
        other = execute(changed['query'],LocalEvidence(changed['graph']))
        for r in (result,other):
            r['cost'].pop('elapsed_seconds',None)
            for s in r['trace']: s['cost'].pop('elapsed_seconds',None)
        self.assertEqual(result,other)

    def test_budget_exactly_at_acquired_proof(self):
        q={'start':'a','relations':['r'],'types':[['person']]}
        g={'types':{'b':'person'},'edges':[{'id':'e','source':'a','relation':'r','target':'b','provenance':'fixture'}]}
        self.assertEqual(execute(q,LocalEvidence(g),Config(max_expansions=1))['terminal'],'ANSWER')
        self.assertEqual(execute(q,LocalEvidence(g),Config(max_expansions=0))['terminal'],'ABSTAIN')

    def test_caps_and_trace_contract(self):
        record=self.records[0]
        for bits in range(16):
            c=Config(*[b=='1' for b in f'{bits:04b}'],max_expansions=2,max_checks=4)
            result=execute(record['query'],LocalEvidence(record['graph']),c)
            self.assertLessEqual(result['cost']['expansions'],2)
            self.assertLessEqual(result['cost']['checks'],4)
            self.assertIn(result['terminal'],('ANSWER','ABSTAIN'))
            for s in result['trace']:
                self.assertTrue({'state_hash_before','state_hash_after','chosen_action','evidence_added','cost'} <= s.keys())

    def test_missing_provenance_and_unobserved_evidence_fail(self):
        q={'start':'a','relations':['r'],'types':[[]]}
        self.assertFalse(check(q,['e'],{}, {})['complete'])
        e={'id':'e','source':'a','relation':'r','target':'b','provenance':''}
        self.assertFalse(check(q,['e'],{'e':e}, {})['complete'])

    def test_na_denominator(self):
        self.assertIsNone(ratio(0,0)['value'])

    def test_timeout_and_invalid_budgets(self):
        r=self.records[0]
        result=execute(r['query'],LocalEvidence(r['graph']),Config(seconds=0))
        self.assertEqual(result['reason'],'timeout')
        with self.assertRaises(ValueError): Config(max_checks=-1)

    def test_parse_failure_is_never_accepted(self):
        r=self.records[0]
        result=execute(r['query'],LocalEvidence(r['graph']),Config(parse_error_rate=1))
        self.assertEqual(result['terminal'],'ABSTAIN')

    def test_duplicate_evidence_ids_rejected(self):
        g=copy.deepcopy(self.records[0]['graph']);g['edges'].append(g['edges'][0])
        with self.assertRaises(ValueError):LocalEvidence(g)


if __name__ == '__main__': unittest.main()
