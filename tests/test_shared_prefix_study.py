import json
from pathlib import Path
import unittest
from flagship_controller.shared_prefix_study import replay, PrefixGraph
from flagship_controller.webqsp_runtime import Blocked


class SharedPrefixTests(unittest.TestCase):
    def test_original_fixed_runs_replay_without_network_or_changed_answers(self):
        root=Path(__file__).resolve().parents[1]/'results/paired-pilot-001'
        records={r['id']:r for r in map(json.loads,(root/'inputs.jsonl').read_text().splitlines())}
        plan=json.loads((root/'plan.json').read_text())
        rows=[r for r in map(json.loads,(root/'predictions.jsonl').read_text().splitlines()) if r['variant']=='fixed']
        for baseline in rows:
            with self.subTest(id=baseline['id']):
                result=replay(records[baseline['id']],baseline,'http://invalid','http://invalid',plan['model'],plan['snapshot'],'fixed')
                for key in ('terminal','reason','answers','witnesses'):
                    self.assertEqual(result[key],baseline[key])
                for key in ('model_calls','model_tokens','graph_calls'):
                    self.assertEqual(result['cost'][key],baseline['cost'][key])
                self.assertEqual(result['cost']['physical_new_model_calls'],0)
                self.assertEqual(result['cost']['physical_new_graph_calls'],0)

    def test_changed_graph_query_rejected_instead_of_silent_replay(self):
        graph=PrefixGraph('http://invalid','snapshot',[{'query':'different','rows':[]}])
        with self.assertRaisesRegex(Blocked,'shared_prefix_graph_mismatch'):
            graph.select('SELECT * WHERE {}')
