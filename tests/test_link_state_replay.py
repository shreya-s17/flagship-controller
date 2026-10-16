import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from flagship_controller.link_state_replay import extract,ReplayGraph,ReplayModel
from flagship_controller.webqsp_runtime import Blocked,NS

ROOT=Path(__file__).resolve().parents[1]


class LinkStateReplayTests(unittest.TestCase):
    def setUp(self):
        self.prefix=extract(ROOT/'results/baseline-dev-002','WebQTrn-562')

    def test_archived_prefix_has_only_charged_link_calls_not_search(self):
        self.assertEqual(self.prefix['cost']['model_calls'],1)
        self.assertTrue(all(e['action'] in ('PARSE','LINK','DISAMBIGUATE','EXCLUDE_ANSWER_CATEGORY') for e in self.prefix['events']))
        self.assertEqual(len(self.prefix['graph_audit']),self.prefix['cost']['graph_calls'])
        self.assertNotIn('gold',self.prefix)

    def test_original_contract_validation_reconstructs_model_and_graph_state_offline(self):
        graph=ReplayGraph(self.prefix);model=ReplayModel(self.prefix,graph)
        with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
            from flagship_controller.structured_runtime import EXTRACT
            parsed=model.ask(EXTRACT,{'question':self.prefix['record']['question']})
        self.assertEqual(parsed,self.prefix['events'][0]['parsed'])
        self.assertEqual(model.contract,graph.question_contract)
        self.assertEqual(model.calls,1)
        self.assertEqual(model.tokens,self.prefix['cost']['model_tokens'])
        with self.assertRaisesRegex(Blocked,'boundary'):model.direct('new request',{},{} )

    def test_graph_query_mismatch_and_exhaustion_never_fall_through_to_network(self):
        graph=ReplayGraph(self.prefix)
        with self.assertRaisesRegex(Blocked,'graph_mismatch'):graph.select('SELECT wrong')
        self.assertEqual(graph.calls,0)
        body=graph.saved[0]['query'].removeprefix('PREFIX ns: <'+NS+'>\n')
        with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
            self.assertEqual(graph.select(body),graph.saved[0]['rows'])
            with self.assertRaisesRegex(Blocked,'boundary'):graph.select(body)
        self.assertEqual(graph.calls,1)

    def test_model_prompt_mismatch_is_not_replayed_or_silently_retried(self):
        graph=ReplayGraph(self.prefix);model=ReplayModel(self.prefix,graph)
        with self.assertRaisesRegex(Blocked,'model_mismatch'):model.direct('wrong prompt',{},{} )
        self.assertEqual(model.calls,0)

    def test_disambiguation_replays_the_original_contract_augmented_prompt(self):
        prefix=copy.deepcopy(self.prefix);inputs={'question':'Fixture?','question_contract':{'fixture':True}}
        prompt={'instruction':'Choose only supplied entity','inputs':inputs}
        prefix['model_audit']=[{'prompt':prompt,'prompt_sha256':hashlib.sha256(json.dumps(prompt,sort_keys=True).encode()).hexdigest(),
            'response':'{"entity":"m.fixture","supported":true}','input_tokens':10,'output_tokens':5}]
        graph=ReplayGraph(prefix);model=ReplayModel(prefix,graph);model.contract={'fixture':True}
        result=model.ask('Choose only supplied entity',{'question':'Fixture?'})
        self.assertEqual(result['entity'],'m.fixture');self.assertEqual(model.tokens,15)

    def test_replayed_incomplete_query_and_over_budget_usage_fail_closed(self):
        prefix=copy.deepcopy(self.prefix);prefix['graph_audit'][0]['sql_state']='S1TAT'
        graph=ReplayGraph(prefix);body=graph.saved[0]['query'].removeprefix('PREFIX ns: <'+NS+'>\n')
        with self.assertRaisesRegex(Blocked,'incomplete'):graph.select(body)
        graph=ReplayGraph(self.prefix);model=ReplayModel(self.prefix,graph);model.max_tokens=1
        from flagship_controller.structured_runtime import EXTRACT
        with self.assertRaisesRegex(Blocked,'budget_exceeded'):model.ask(EXTRACT,{'question':self.prefix['record']['question']})

if __name__=='__main__':unittest.main()
