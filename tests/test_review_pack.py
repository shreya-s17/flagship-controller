from pathlib import Path
import json
import tempfile
import unittest
from flagship_controller.review_pack import prepare


class ReviewPackTests(unittest.TestCase):
    def test_mask_policy_score_and_model_critique_keep_ground_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);study=root/'study';study.mkdir()
            (study/'inputs.jsonl').write_text(json.dumps({'id':'q','question':'Where is Example?','split':'pilot'})+'\n')
            record={'id':'q','variant':'repair','terminal':'ANSWER','answers':['m.answer'],'witnesses':[['observed']],
                'trace':[{'action':'PLAN','program':{'steps':[],'explanation':'biased model explanation'}},
                         {'action':'SEMANTIC_VERIFY','gate':{'reason':'biased model critique'}}],
                'model_audit':['secret critique'],'gold':['not disclosed'],'f1':1,
                'cost':{'model_calls':1,'graph_calls':2,'model_tokens':3}}
            (study/'predictions.jsonl').write_text(json.dumps(record)+'\n')
            result=prepare([study],root/'pack');self.assertEqual(result['cases'],1)
            text=(root/'pack/reviewer/cases.jsonl').read_text();case=json.loads(text)
            for name in ['variant','f1','gold','model_audit','critique','explanation']:self.assertNotIn(name,text)
            self.assertEqual(case['witnesses'],[['observed']]);self.assertEqual(case['review']['answer_scope'],'unknown')
            self.assertEqual((root/'pack/owner-key.json').stat().st_mode&0o777,0o600)
            with self.assertRaises(ValueError):prepare([study],root/'pack')
