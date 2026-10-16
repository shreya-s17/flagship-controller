import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('common_analysis',ROOT/'scripts/summarize_common_study.py')
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)


class CommonAnalysisTests(unittest.TestCase):
    def test_seed_repeats_average_within_question_and_controls_are_not_benchmark_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);(folder/'journal').mkdir();rows=[];order=[]
            for seed in (17,29):
                for qid in ('WebQTrn-fixture','hand-negative'):
                    for policy in ('fixed','repair','semantic-gate-off','reason-text-off','tog-declared-json'):
                        item={'id':qid,'seed':seed,'variant':policy};order.append(item)
                        answer=policy!='fixed' or seed==17
                        rows.append({**item,'terminal':'ANSWER' if answer else 'ABSTAIN','answers':['a'] if answer else [],
                            'reason':'synthetic fixture','cost':{'model_calls':1,'model_tokens':10,'graph_calls':1,
                                'elapsed_seconds':1.,'physical_new_model_calls':1,'model_usage_complete':True}})
            (folder/'manifest.json').write_text(json.dumps({'order':order,'seeds':[17,29],'question_ids':['WebQTrn-fixture','hand-negative']}))
            (folder/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            label={'id':'WebQTrn-fixture','parses':[{'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},'Answers':[{'AnswerArgument':'a'}]}]}
            gold=folder/'gold.jsonl';gold.write_text(json.dumps(label)+'\n')
            result=analysis.analyze(folder,gold)
            self.assertEqual(result['official_original_questions'],1)
            self.assertEqual(result['repair_minus_fixed_mean_question_f1'],.5)
            self.assertIsNone(result['confidence_interval']);self.assertIsNone(result['stop_recovery_rates'])
            self.assertEqual(result['methods']['fixed']['question_means'][0]['seeds'],2)
            (folder/'predictions.jsonl').write_text(json.dumps(rows[0])+'\n')
            with self.assertRaises(ValueError):analysis.analyze(folder,gold)

if __name__=='__main__':unittest.main()
