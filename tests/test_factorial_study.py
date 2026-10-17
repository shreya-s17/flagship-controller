import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from flagship_controller import factorial_runtime as runtime, factorial_study as study, factorial_audit, factorial_analysis
from flagship_controller.obligation_stress import program, ATTRACTION, MEMBER, PARENT
from flagship_controller.webqsp_runtime import Blocked


class FactorialTests(unittest.TestCase):
    def inputs(self, folder, split='pilot'):
        path = Path(folder) / 'input.jsonl'
        path.write_text(json.dumps({'id': 'fixture', 'question': "Who are Ada's parents?", 'split': split}) + '\n')
        return path

    def test_catalog_off_acquires_nothing_and_keeps_guard_independent(self):
        root = {'relation': ATTRACTION, 'direction': 'out'}
        graph = runtime.FactorialGraph('offline://', 'fixture', catalog_mode='off')
        graph.question_contract = {'answer_category': 'location'}
        with patch.object(graph, 'select', side_effect=AssertionError('Catalog-off must not acquire')):
            catalog = graph.catalog('Which attractions are in Paris?', [root], [], ['m.city'], [{'mention': 'Paris'}], {})
        self.assertTrue(graph.obligation)
        self.assertFalse(graph.primary_join_options)
        self.assertFalse(any(c['program']['constraints'] for c in catalog))
        with self.assertRaisesRegex(Blocked, 'missing_primary_membership'):
            graph.check_obligation(catalog[0]['program'])
        graph.guard_enabled = False;graph.check_obligation(catalog[0]['program'])

    def test_catalog_on_observes_membership_without_changing_other_guards(self):
        graph = runtime.FactorialGraph('offline://', 'fixture', catalog_mode='on', guard_enabled=False)
        graph.question_contract = {'answer_category': 'location'}
        graph.select = lambda query: [{'relation': {'value': runtime.parent.NS + MEMBER}, 'direction': {'value': 'out'}}]
        catalog = graph.catalog('Which attractions are in Paris?', [{'relation': ATTRACTION, 'direction': 'out'}], [], ['m.city'], [{'mention': 'Paris'}], {})
        self.assertTrue(catalog[0]['program']['constraints'])
        with self.assertRaises(Blocked):
            runtime.parent.compile_program(['m.city', 'm.other'], catalog[0]['program'])

    def test_boundary_occurs_before_catalog_and_guard_specific_inference(self):
        class Graph(runtime.FactorialGraph):
            def typed_link(self, *args): return ['m.person'], 'fixture'
            def inventory(self, *args): return [{'relation': PARENT, 'direction': 'out'}]
            def schema(self, *args): return []
            def catalog(self, *args): raise AssertionError('Common state crossed catalog boundary')
        class Model:
            calls = 0;tokens = 0;audit = [];semantic_audit = []
            def ask(self, instruction, inputs):
                self.calls += 1
                if instruction.startswith('Extract'):
                    return {'supported': True, 'anchors': [{'mention': 'Ada', 'type_hint': 'person'}], 'obligations': ['parents']}
                if instruction.startswith('Select'):
                    return {'roots': [{'relation': PARENT, 'direction': 'out'}]}
                raise AssertionError('Common state requested a program choice')
        row = runtime.run({'id': 'fixture', 'question': "Who are Ada's parents?", 'split': 'pilot'},
            Graph('offline://', 'fixture'), Model(), variant='fixed',
            on_event=runtime._boundary(None, 'SCHEMA', 'pre_catalog_capture_boundary'))
        self.assertEqual(row['reason'], 'pre_catalog_capture_boundary')
        self.assertEqual(row['cost']['model_calls'], 2)

    def test_condition_and_capture_mismatch_is_fatal(self):
        with self.assertRaisesRegex(ValueError, 'capture mismatch'):
            runtime.continue_policy({'catalog_mode': 'off'}, 'repair-C1G1', 'unused', 'unused')
        with self.assertRaises(ValueError): runtime.settings('invented')

    def test_freeze_has_full_five_condition_denominator_and_nine_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study'
            plan = study.freeze(self.inputs(temp), folder, 'fixture', seeds=(17, 29))
            self.assertEqual(len(plan['order']), 10)
            self.assertEqual(len(plan['source_hashes']), 9)
            self.assertEqual(set(p['variant'] for p in plan['order']), set(runtime.POLICIES))
            self.assertEqual(study.validate(folder)[0], plan)
            with self.assertRaises(ValueError): study.freeze(self.inputs(temp), folder, 'fixture')

    def test_reserved_and_test_are_refused(self):
        for split in ('train_remaining', 'test', 'reserved'):
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaisesRegex(ValueError, 'pilot'):
                    study.freeze(self.inputs(temp, split), Path(temp) / 'study', 'fixture')

    def test_mutation_is_rejected_before_any_environment_request(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';study.freeze(self.inputs(temp), folder, 'fixture')
            (folder / 'manifest.json').write_text('{}')
            with patch.object(study, 'verify_environment', side_effect=AssertionError('Too late')):
                with self.assertRaisesRegex(ValueError, 'manifest changed'):
                    study.execute(folder, 'unused', 'unused')

    def test_materialized_runtime_loads_without_evaluators_or_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';study.freeze(self.inputs(temp), folder, 'fixture')
            script = Path(__file__).resolve().parents[1] / 'scripts/materialize_factorial_study.py'
            spec = importlib.util.spec_from_file_location('restore_factorial', script)
            module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            target = Path(temp) / 'isolated'
            self.assertEqual(module.materialize(folder, target), 9)
            result = subprocess.run(['python3', '-m', 'flagship_controller.factorial_study', 'freeze', '--help'], cwd=target, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((target / 'flagship_controller/official_score.py').exists())
            with self.assertRaises(ValueError): module.materialize(folder, target)

    def test_durable_stages_and_completed_resume_make_no_duplicate_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';study.freeze(self.inputs(temp), folder, 'fixture')
            def packet(record, *args):
                return {'record': record, 'seed': 17, 'model': 'fixture', 'snapshot': 'fixture', 'internal_ready': True,
                        'internal': {'cost': {'model_calls': 2, 'model_tokens': 10, 'graph_calls': 3}, 'seconds': 1.}}
            def catalog(common, mode, *args):
                return {**common, 'catalog_mode': mode, 'common_sha256': runtime.parent.digest(common)}
            def outcome(capture, policy, *args):
                return {'id': 'fixture', 'variant': policy, 'terminal': 'ABSTAIN', 'reason': 'fixture', 'cost': {}}
            with patch.object(study, 'verify_environment'), patch.object(runtime, 'capture_common', side_effect=packet) as common, patch.object(runtime, 'capture_catalog', side_effect=catalog) as branches, patch.object(runtime, 'continue_policy', side_effect=outcome) as policy:
                study.execute(folder, 'unused', 'unused');study.execute(folder, 'unused', 'unused')
                self.assertEqual(common.call_count, 1)
                self.assertEqual(branches.call_count, 2)
                self.assertEqual(policy.call_count, 5)
            self.assertEqual(len((folder / 'predictions.jsonl').read_text().splitlines()), 5)

    def test_interrupted_common_capture_retains_unknowns_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';plan = study.freeze(self.inputs(temp), folder, 'fixture')
            jobs = folder / 'journal';jobs.mkdir()
            key = '17-' + study.old.sha(b'fixture')[:16]
            study.old.write_json(jobs / (key + '-common.started.json'), {'item': {'id': 'fixture', 'seed': 17, 'stage': 'pre_catalog'}})
            with patch.object(study, 'verify_environment'), patch.object(runtime, 'capture_common', side_effect=AssertionError('No retry')):
                study.execute(folder, 'unused', 'unused')
            rows = list(map(json.loads, (folder / 'predictions.jsonl').read_text().splitlines()))
            self.assertEqual(len(rows), 5)
            self.assertTrue(all(r['cost']['cost_is_lower_bound'] for r in rows))
            self.assertTrue(all(not r['policy_continuation_executed'] for r in rows))

    def test_replay_cursor_mismatch_halts_instead_of_silently_branching(self):
        class State:
            cursor = 0;saved = [{}];prefix = []
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            runtime._assert_consumed(State(), State(), {'reason': 'fixture'})

    def test_real_seeded_transport_replays_nested_boundaries_and_distinct_catalogs(self):
        class Graph(runtime.FactorialGraph):
            def typed_link(self, *args):
                self.select('fixture-link');return ['m.city'], 'fixture'
            def inventory(self, *args):
                self.select('fixture-inventory');return [{'relation': ATTRACTION, 'direction': 'out'}]
            def schema(self, *args):
                self.select('fixture-schema');return []
            def select(self, body):
                if self.cursor < len(self.saved):
                    return super().select(body)
                if body.startswith('SELECT DISTINCT ?relation ?direction'):
                    rows = [{'relation': {'value': runtime.parent.NS + MEMBER}, 'direction': {'value': 'out'}}]
                elif body.startswith('SELECT DISTINCT ?v1 WHERE'):
                    rows = [{'v1': {'type': 'uri', 'value': runtime.parent.NS + 'm.attraction'}}]
                else:
                    rows = []
                self.calls += 1
                self.audit.append({'query': 'PREFIX ns: <' + runtime.parent.NS + '>\n' + body,
                                   'rows': copy.deepcopy(rows), 'snapshot': self.snapshot, 'sql_state': '00000'})
                return rows
        requests = []
        def provider(url, payload, timeout):
            requests.append(copy.deepcopy(payload))
            prompt = json.loads(payload['messages'][0]['content'])
            instruction, inputs = prompt['instruction'], prompt['inputs']
            if instruction.startswith('Extract all'):
                value = {'supported': True, 'anchors': [{'mention': 'Paris', 'type_hint': 'location'}],
                         'answer_category': 'location', 'requirements': [
                             {'kind': 'answer_type', 'span': 'attractions', 'description': 'Requested attractions'},
                             {'kind': 'relation', 'span': 'in', 'description': 'Within the copied place'}]}
            elif instruction.startswith('Select up to'):
                value = {'root_indices': [0]}
            elif instruction.startswith('Choose a program'):
                value = {'program_index': inputs['programs'][0]['index']}
            elif instruction.startswith('Evaluate EVERY'):
                value = {'verdicts': [{'index': i, 'status': 'satisfied', 'evidence_steps': [0], 'reason': 'fixture'} for i in range(2)]}
            else:
                raise AssertionError('Unexpected model request: ' + instruction)
            return {'message': {'content': json.dumps(value)}, 'prompt_eval_count': 10, 'eval_count': 5}
        record = {'id': 'fixture', 'question': 'Which attractions are in Paris?', 'split': 'pilot'}
        with patch.object(runtime, 'FactorialGraph', Graph), patch.object(study.old.webqsp_runtime, 'post_json', side_effect=provider):
            common = runtime.capture_common(record, 'offline://', 'offline://', 'fixture', 'fixture', 17)
            self.assertTrue(common['internal_ready'], common['capture_result'])
            self.assertFalse(any(e['action'] == 'PLAN' for e in common['capture_result']['trace']))
            self.assertEqual(len(requests), 2)
            captures = {mode: runtime.capture_catalog(common, mode, 'offline://', 'offline://') for mode in ('off', 'on')}
            self.assertEqual(len(requests), 4)
            plans = {mode: next(e['program'] for e in p['capture_result']['trace'] if e['action'] == 'PLAN') for mode, p in captures.items()}
            self.assertFalse(plans['off']['constraints']);self.assertTrue(plans['on']['constraints'])
            self.assertEqual(captures['off']['physical_stage']['graph_calls'], 0)
            self.assertEqual(captures['on']['physical_stage']['graph_calls'], 1)
            rows = [runtime.continue_policy(captures[runtime.settings(p)[0]], p, 'offline://', 'offline://') for p in runtime.POLICIES]
            self.assertEqual([r['terminal'] for r in rows], ['ANSWER', 'ABSTAIN', 'ANSWER', 'ANSWER', 'ANSWER'])
            self.assertEqual(rows[1]['reason'], 'program_catalog_exhausted')
            self.assertEqual(len(requests), 8)  # 2 shared + 2 catalog choices + 4 final audits.
            self.assertTrue(all(p['options']['seed'] == 17 for p in requests))
            for row in rows:
                self.assertEqual(row['shared_state']['common_pre_catalog_sha256'], runtime.parent.digest(common))
                self.assertEqual(row['cost']['physical_new_model_calls'], int(row['terminal'] == 'ANSWER'))
            bad = copy.deepcopy(captures['on']);bad['internal']['provider_audit'][0]['payload_sha256'] = 'tampered'
            with self.assertRaisesRegex(ValueError, 'replay mismatch'):
                runtime.continue_policy(bad, 'fixed-C1G1', 'offline://', 'offline://')
            # Execute the full durable harness with real seeded transport/replay
            # and the controlled provider/graph above, then audit independently.
            with tempfile.TemporaryDirectory() as temp:
                inputs = Path(temp) / 'inputs.jsonl';inputs.write_text(json.dumps(record) + '\n')
                folder = Path(temp) / 'study';study.freeze(inputs, folder, 'fixture')
                with patch.object(study, 'verify_environment'):
                    study.execute(folder, 'offline://', 'offline://')
                checked = factorial_audit.check(folder)
                self.assertEqual((checked['rows_checked'], checked['common_captures'], checked['catalog_captures']), (5, 1, 2))
                gold = Path(temp) / 'gold.jsonl';gold.write_text('')
                summary = factorial_analysis.analyze(folder, gold)
                self.assertEqual(summary['physical']['model_attempts']['total_known_lower_bound'], 8)
                self.assertEqual(summary['physical']['graph_calls']['total_known_lower_bound'], 12)
                self.assertTrue(summary['physical']['model_attempts']['complete'])
                self.assertIsNone(summary['descriptive_f1_contrasts'])
                # Recompute ordinary hashes after tampering, so the independent
                # nested linkage check must detect this semantic ledger error.
                path = folder / 'journal/policy-0000.json';env = json.loads(path.read_text())
                env['value']['shared_state']['catalog_packet_sha256'] = 'wrong'
                env['sha256'] = runtime.parent.digest(env['value']);study.old.write_json(path, env)
                rows = list(map(json.loads, (folder / 'predictions.jsonl').read_text().splitlines()))
                rows[0]['shared_state']['catalog_packet_sha256'] = 'wrong'
                (folder / 'predictions.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
                completion = json.loads((folder / 'completion.json').read_text())
                completion['predictions_sha256'] = study.old.sha((folder / 'predictions.jsonl').read_bytes())
                study.old.write_json(folder / 'completion.json', completion)
                with self.assertRaisesRegex(ValueError, 'nested prefix identity'):
                    factorial_audit.check(folder)


if __name__ == '__main__':
    unittest.main()
