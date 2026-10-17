import copy
import unittest
from unittest.mock import patch
from flagship_controller import catalog_intervention_audit as audit
from flagship_controller.obligation_stress import program, PARENT, ATTRACTION, MEMBER


class CatalogContrastTests(unittest.TestCase):
    def packet(self):
        roots = [{'relation': ATTRACTION, 'direction': 'out'}]
        old = audit.runtime.base.rank_catalog('What to see in Paris?',
            audit.runtime.base.program_catalog(roots, [], 1, {}, 'What to see in Paris?'), limit=20)
        return {'internal_ready': True, 'record': {'id': 'fixture', 'question': 'What to see in Paris?'},
                'seed': 17, 'internal': {'model_audit': [{'prompt': {'instruction': 'Choose a program',
                    'inputs': {'anchors': [{'mention': 'Paris', 'index': 0}]}}}]},
                'capture_result': {'trace': [
                    {'action': 'LINK', 'candidates': ['m.city']},
                    {'action': 'SCHEMA', 'roots': roots, 'schema': []},
                    {'action': 'PRIMARY_ANCHOR_JOIN_INVENTORY', 'obligation': {'kind': 'location_membership'}},
                    {'action': 'PROGRAM_CATALOG', 'programs': old}]}}

    def test_identical_catalog_is_not_a_counterfactual_score(self):
        result = audit.contrast(self.packet())
        self.assertTrue(result['catalogs_structurally_equal'])
        self.assertEqual(result['schema_only_rule_compatible'], 0)
        self.assertIn('not evaluated', result['answer_correctness'])

    def test_observed_membership_addition_changes_availability_only(self):
        packet = self.packet()
        packet['capture_result']['trace'][-1]['programs'].append(
            {'program': program(ATTRACTION, join=(MEMBER, 'out'))})
        result = audit.contrast(packet)
        self.assertEqual(len(result['added_programs']), 1)
        self.assertEqual(result['expanded_rule_compatible'], 1)
        self.assertEqual(result['schema_only_rule_compatible'], 0)

    def test_anchor_mismatch_fails_instead_of_guessing(self):
        packet = self.packet()
        packet['internal']['model_audit'][0]['prompt']['inputs']['anchors'].append({'index': 1})
        with self.assertRaisesRegex(ValueError, 'anchor count'):
            audit.contrast(packet)

    def test_constraint_order_is_not_a_new_program(self):
        p = program(PARENT)
        p['constraints'] = [{'at': 1, 'anchor': 0, 'relation': 'r', 'direction': 'in'},
                            {'at': 1, 'anchor': 0, 'relation': 's', 'direction': 'out'}]
        other = copy.deepcopy(p);other['constraints'].reverse()
        self.assertEqual(audit.signature({'program': p}), audit.signature({'program': other}))


if __name__ == '__main__':
    unittest.main()
