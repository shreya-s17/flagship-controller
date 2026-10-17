import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from flagship_controller import obligation_stress as stress
from flagship_controller.webqsp_runtime import Blocked


class StressAuditTests(unittest.TestCase):
    def test_reference_interpreter_is_independent_of_production_compiler(self):
        edges = {(0, stress.PARENT, 1), (1, stress.CHILD, 0), (1, stress.IDENTITY, 1)}
        with patch.object(stress.runtime, 'compile_program', side_effect=AssertionError('Not an oracle')):
            self.assertEqual(stress.interpret(edges, stress.program(stress.PARENT)), {1})
            self.assertEqual(stress.interpret(edges, stress.program(stress.CHILD, 'in')), {1})
            self.assertEqual(stress.interpret(edges, stress.program(stress.PARENT, identity=True)), {1})
            self.assertEqual(stress.interpret(edges, stress.program(stress.PARENT, filtered=True)), set())

    def test_counterexamples_are_retained_without_calling_them_pipeline_errors(self):
        report = stress.evaluate([], nodes=2)
        self.assertTrue(report['integrity_pass'])
        self.assertEqual(report['kinship']['worlds'], 4)
        self.assertEqual(report['kinship']['counts']['evaluated'], 64)
        self.assertEqual(report['location']['worlds'], 216)
        self.assertEqual(report['location']['counts']['evaluated'], 2160)
        self.assertGreater(report['kinship']['by_case']['parents/parents-identity']['rejected_exact_nonempty'], 0)
        self.assertGreater(report['location']['by_case']['downtown/containedby']['passed_inexact_nonempty'], 0)
        self.assertFalse(report['publication_ready'])

    def test_audit_detects_accept_everything_and_reject_everything_mutations(self):
        accept = stress.evaluate([], nodes=2, checker=lambda *args: None)
        self.assertFalse(accept['integrity_pass'])
        def reject(*args):
            raise Blocked('mutated')
        self.assertFalse(stress.evaluate([], nodes=2, checker=reject)['integrity_pass'])

    def test_grammar_does_not_silently_count_a_new_rule_as_unhandled(self):
        case = {'case_id': 'unknown', 'question': 'Which siblings?', 'mentions': [],
                'category': 'person', 'expected': None}
        report = stress.grammar_audit([case], lambda *args: {'kind': 'invented'})
        self.assertEqual(report['matching'], 0)

    def test_freeze_rejects_input_and_manifest_mutation_before_enumeration(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'audit'
            stress.freeze(folder, [])
            (folder / 'grammar-cases.json').write_text('[{}]')
            with patch.object(stress, 'evaluate', side_effect=AssertionError('Too late')):
                with self.assertRaisesRegex(ValueError, 'inputs changed'):
                    stress.execute(folder)
            (folder / 'manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                stress.execute(folder)

    def test_source_mutation_and_overlarge_world_are_rejected(self):
        with self.assertRaises(ValueError):
            stress.evaluate([], nodes=5)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'audit'
            stress.freeze(folder, [])
            manifest = json.loads((folder / 'manifest.json').read_text())
            manifest['source_hashes']['obligation_runtime.py'] = '0' * 64
            (folder / 'manifest.json').write_text(json.dumps(manifest))
            (folder / 'manifest.sha256').write_text(stress.sha(folder / 'manifest.json'))
            with self.assertRaisesRegex(ValueError, 'source changed'):
                stress.execute(folder)


if __name__ == '__main__':
    unittest.main()
