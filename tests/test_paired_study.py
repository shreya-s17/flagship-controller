import json
from pathlib import Path
import tempfile
import unittest
from flagship_controller.paired_study import freeze,execute

class PairedStudyTests(unittest.TestCase):
    def test_frozen_order_has_both_variants_without_gold(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);inputs=d/'inputs.jsonl'
            inputs.write_text(json.dumps({'id':'q','question':'Where is Example?','split':'pilot'})+'\n')
            plan=freeze(inputs,d/'study',['q'],'model','snapshot')
            self.assertEqual({(r['id'],r['variant']) for r in plan['order']},{('q','fixed'),('q','repair')})
            self.assertTrue((d/'study/runtime-source.py').exists())
            with self.assertRaises(ValueError):freeze(inputs,d/'study',['q'],'model','snapshot')
    def test_no_gold_or_official_test_input(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);inputs=d/'input.jsonl'
            for record in [{'id':'q','question':'Q','split':'test'}, {'id':'q','question':'Q','split':'pilot','parses':[]}]:
                inputs.write_text(json.dumps(record)+'\n')
                with self.assertRaises(ValueError):freeze(inputs,d/'out',['q'],'model','snapshot')
    def test_missing_and_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);inputs=d/'input.jsonl';inputs.write_text(json.dumps({'id':'q','question':'Q','split':'pilot'})+'\n')
            for ids in [['missing'],['q','q']]:
                with self.assertRaises(ValueError):freeze(inputs,d/'out',ids,'model','snapshot')

class PairedAnalysisTests(unittest.TestCase):
    def test_complete_pair_and_offline_delta(self):
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'scripts/summarize_paired_study.py'
        spec=importlib.util.spec_from_file_location('paired_analysis',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);order=[{'id':'fixture','variant':v} for v in ['fixed','repair']]
            (folder/'plan.json').write_text(json.dumps({'order':order,'question_ids':['fixture']}))
            rows=[]
            for v in ['fixed','repair']:
                rows.append({'id':'fixture','variant':v,'terminal':'ANSWER' if v=='repair' else 'ABSTAIN',
                  'answers':['answer'] if v=='repair' else [],'reason':'fixture','trace':[],
                  'cost':{'graph_calls':1,'model_calls':1,'model_tokens':10,'elapsed_seconds':1.,'model_usage_complete':True}})
            (folder/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            gold=folder/'gold.jsonl';gold.write_text(json.dumps({'id':'fixture','parses':[{'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},'Answers':[{'AnswerArgument':'answer'}]}]})+'\n')
            result=module.analyze(folder,gold)
            self.assertEqual(result['paired_f1_delta']['mean'],1.)
            self.assertIsNone(result['stop_error_rates'])
            (folder/'predictions.jsonl').write_text(json.dumps(rows[0])+'\n')
            with self.assertRaises(ValueError):module.analyze(folder,gold)
