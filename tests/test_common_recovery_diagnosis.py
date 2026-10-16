import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('recovery_diagnosis', Path(__file__).resolve().parents[1]/'scripts/diagnose_common_recovery.py')
diagnosis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnosis)


class RecoveryDiagnosisTests(unittest.TestCase):
    def row(self, trace, terminal='ANSWER'):
        return {'id': 'fixture', 'seed': 17, 'variant': 'repair', 'trace': trace,
                'terminal': terminal, 'reason': 'fixture', 'answers': ['x'] if terminal == 'ANSWER' else []}

    def test_provisional_exact_answer_then_rejection_is_not_recovery(self):
        trace = [{'action': 'PLAN', 'program_index': 0, 'program': {}},
                 {'action': 'ACQUIRE', 'answers': ['x']},
                 {'action': 'REJECT', 'reason': 'semantic_verifier_reject'}]
        result = diagnosis.describe(self.row(trace, 'ABSTAIN'), {'scorable': True, 'exact_f1': 0})
        self.assertFalse(result['answered_after_recorded_rejection'])
        self.assertFalse(result['official_exact_after_recorded_rejection'])
        self.assertEqual(result['attempts'][0]['acquired_answers'], ['x'])

    def test_exact_after_revision_is_not_semantic_certification(self):
        trace = [{'action': 'PLAN', 'program_index': 0, 'program': {}},
                 {'action': 'REJECT', 'reason': 'missing_support'},
                 {'action': 'REPAIR_PLAN', 'program_index': 1, 'program': {}},
                 {'action': 'ACQUIRE', 'answers': ['x']}]
        result = diagnosis.describe(self.row(trace), {'scorable': True, 'exact_f1': 1})
        self.assertTrue(result['official_exact_after_recorded_rejection'])
        self.assertIsNone(result['independent_semantic_recovery'])

    def test_answer_after_revision_can_remain_wrong_or_unscored(self):
        trace = [{'action': 'PLAN', 'program_index': 0, 'program': {}},
                 {'action': 'REJECT', 'reason': 'missing_support'},
                 {'action': 'REPAIR_PLAN', 'program_index': 1, 'program': {}}]
        for score in (None, {'scorable': True, 'exact_f1': 0}):
            result = diagnosis.describe(self.row(trace), score)
            self.assertTrue(result['answered_after_recorded_rejection'])
            self.assertFalse(result['official_exact_after_recorded_rejection'])

    def test_unrejected_revision_is_invalid_evidence(self):
        with self.assertRaisesRegex(ValueError, 'preceding recorded rejection'):
            diagnosis.describe(self.row([{'action': 'REPAIR_PLAN', 'program_index': 1, 'program': {}}]))
