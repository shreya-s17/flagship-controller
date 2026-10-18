import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from flagship_controller import benchmark_study as study, benchmark_runtime as runtime
from flagship_controller import benchmark_analysis as analysis

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'evaluation/reserved-training-100-v2/inputs.jsonl'


class BenchmarkTests(unittest.TestCase):
    def freeze(self, folder):
        with patch.object(study.tog_adapter, 'load_upstream'):
            return study.freeze(INPUTS, folder, 'fixture', 'fixture')

    def test_exact_reservation_full_denominator_and_outcome_free_review_sample(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';plan = self.freeze(folder)
            self.assertEqual(len(plan['order']), 1800)
            self.assertEqual(len(plan['source_hashes']), 15)
            self.assertEqual(plan['seeds'], [17, 29, 43])
            self.assertEqual(len(plan['semantic_review']['question_ids']), 20)
            self.assertEqual(plan['semantic_review']['records_expected'], 120)
            self.assertEqual(study.validate(folder)[0], plan)
            self.assertTrue(all(r['split'] == 'train_remaining' for r in study.validate(folder)[1].values()))
            self.assertNotIn('official_score.py', plan['source_hashes'])

    def test_wrong_bytes_test_data_and_labels_are_refused(self):
        for data in (b'', b'{"id":"x","question":"Q","split":"test"}\n',
                     INPUTS.read_bytes().replace(b'train_remaining', b'pilot', 1)):
            with self.assertRaisesRegex(ValueError, 'exact pre-reserved'):
                study.records_from(data)

    def test_manifest_source_and_input_tampering_fail_before_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';self.freeze(folder)
            (folder / 'manifest.json').write_text('{}')
            with patch.object(study.helpers, 'verify_environment', side_effect=AssertionError('No request')):
                with self.assertRaisesRegex(ValueError, 'manifest changed'):
                    study.execute(folder, 'fixture', 'unused', 'unused')

    def test_materialized_sources_load_without_annotation_or_scorer(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';self.freeze(folder)
            spec = importlib.util.spec_from_file_location('restore_benchmark', ROOT / 'scripts/materialize_benchmark_study.py')
            m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            target = Path(temp) / 'runtime';self.assertEqual(m.materialize(folder, target), 15)
            result = subprocess.run(['python3', '-m', 'flagship_controller.benchmark_study', '--help'], cwd=target, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((target / 'flagship_controller/official_score.py').exists())

    def test_window_boundary_and_resume_never_repeat_admitted_or_committed_work(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'study';plan = self.freeze(folder)
            def capture(record, endpoint, url, model, snapshot, seed, observer):
                return runtime.interrupted_capture(record, seed, model, snapshot, None)
            with patch.object(study.helpers, 'verify_environment'), patch.object(study.tog_adapter, 'load_upstream'), \
                 patch.object(study.time, 'monotonic', side_effect=[0, 0, 3601]), \
                 patch.object(runtime, 'capture', side_effect=capture) as calls:
                study.execute(folder, 'fixture', 'unused', 'unused', max_hours=1)
                self.assertEqual(calls.call_count, 1)
            rows = list(map(json.loads, (folder / 'predictions.jsonl').read_text().splitlines()))
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(r['cost']['cost_is_lower_bound'] for r in rows))
            self.assertFalse((folder / 'completion.json').exists())
            self.assertEqual(json.loads((folder / 'progress.json').read_text())['planned'], 1800)
            with patch.object(study.helpers, 'verify_environment'), patch.object(study.tog_adapter, 'load_upstream'), \
                 patch.object(study.time, 'monotonic', side_effect=[0, 0, 3601]), \
                 patch.object(runtime, 'capture', side_effect=AssertionError('No repeated capture')):
                study.execute(folder, 'fixture', 'unused', 'unused', max_hours=1)
            self.assertEqual(len((folder / 'predictions.jsonl').read_text().splitlines()), 6)

    def test_real_seeded_link_prefix_is_shared_with_baseline_without_catalog(self):
        class Graph(runtime.factorial.FactorialGraph):
            def typed_link(self, *args):
                self.select('fixture-link');return ['m.person'], 'fixture'
            def inventory(self, *args):
                if self.link_ready:
                    callback = self.link_ready;self.link_ready = None;callback()
                self.select('fixture-inventory');return [{'relation': 'people.person.parents', 'direction': 'out'}]
            def schema(self, *args):
                self.select('fixture-schema');return []
            def select(self, body):
                if self.cursor < len(self.saved):return super().select(body)
                self.calls += 1
                self.audit.append({'query': 'PREFIX ns: <' + study.webqsp_runtime.NS + '>\n' + body,
                    'rows': [], 'snapshot': self.snapshot, 'sql_state': '00000'})
                return []
        requests = []
        def provider(url, payload, timeout):
            requests.append(copy.deepcopy(payload))
            prompt = json.loads(payload['messages'][0]['content'])
            if prompt['instruction'].startswith('Extract all'):
                response = {'supported': True, 'anchors': [{'mention': 'Ada', 'type_hint': 'person'}],
                    'answer_category': 'person', 'requirements': [
                        {'kind': 'answer_type', 'span': 'Who', 'description': 'People requested'},
                        {'kind': 'relation', 'span': 'parents', 'description': 'Parents requested'}]}
            else:
                self.assertTrue(prompt['instruction'].startswith('Select up to'))
                response = {'root_indices': [0]}
            return {'message': {'content': json.dumps(response)}, 'prompt_eval_count': 10, 'eval_count': 5}
        def baseline_run(record, graph, model, upstream, seconds, observer, **kwargs):
            study.common_linker.link_question(record, graph, model, lambda *args, **kw: None)
            return {'id': record['id'], 'terminal': 'ABSTAIN', 'answers': [], 'reason': 'fixture',
                'trace': [], 'graph_audit': graph.audit, 'model_audit': model.audit,
                'cost': {'graph_calls': graph.calls, 'model_calls': model.calls, 'model_tokens': model.tokens,
                         'elapsed_seconds': 0., 'model_usage_complete': True}}
        record = {'id': 'fixture', 'question': "Who are Ada's parents?", 'split': 'pilot'}
        with patch.object(runtime.factorial, 'FactorialGraph', Graph), \
             patch.object(runtime.shared, 'StudyGraph', Graph), \
             patch.object(study.webqsp_runtime, 'post_json', side_effect=provider), \
             patch.object(study.tog_adapter, 'run', side_effect=baseline_run):
            packet = runtime.capture(record, 'unused', 'unused', 'fixture', 'fixture', 17)
            self.assertTrue(packet['internal_ready'], packet['capture_result'])
            self.assertEqual(len(packet['link']['provider_audit']), 1)
            self.assertEqual(len(packet['internal']['provider_audit']), 2)
            self.assertEqual(len(packet['link']['graph_audit']), 1)
            row = runtime.baseline(packet, 'unused', 'unused', 'fixture')
            self.assertEqual(row['shared_state']['prefix_kind'], 'link')
            self.assertEqual(row['cost']['physical_new_model_calls'], 0)
            self.assertEqual(row['cost']['physical_new_graph_calls'], 0)
            self.assertEqual(len(requests), 2)

    def test_analysis_averages_seeds_within_questions_and_retains_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'study';plan=self.freeze(folder)
            rows=[]
            for item in plan['order']:
                answered=item['variant']=='repair-C1G1'
                rows.append({**item,'terminal':'ANSWER' if answered else 'ABSTAIN','answers':['m.fixture'] if answered else [],
                    'cost':{'model_calls':1,'model_tokens':2,'graph_calls':1,'elapsed_seconds':1.,'model_usage_complete':True}})
            (folder/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            gold=Path(temp)/'gold.jsonl'
            gold.write_text(''.join(json.dumps({'id':qid,'parses':[{'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},'Answers':[{'AnswerArgument':'m.fixture'}]}]})+'\n' for qid in plan['question_ids']))
            with patch.object(analysis,'check',return_value={'rows_checked':1800}):
                result=analysis.analyze(folder,gold)
            primary=result['primary_repair_minus_fixed']
            self.assertEqual(primary['question_units'],100)
            self.assertEqual((primary['mean_difference'],primary['lower_95'],primary['upper_95']),(1.,1.,1.))
            self.assertEqual(result['methods']['fixed-C1G1']['submitted_outcomes'],300)
            self.assertIsNone(result['independent_semantic_review'])


if __name__ == '__main__':unittest.main()
