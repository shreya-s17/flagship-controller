import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from flagship_controller.benchmark import prepare


class BenchmarkTests(unittest.TestCase):
    def test_gold_separation_and_duplicate_groups(self):
        q=lambda i,text:{'QuestionId':i,'RawQuestion':text,'ProcessedQuestion':text,
                          'Parses':[{'Answers':['SECRET'],'TopicEntityMid':'SECRET'}]}
        train={'Version':'1.0','FreebaseVersion':'fixture','Questions':
               [q('a','same question'),q('b','same question'),q('c','different')]}
        test={'Questions':[q('d','held out')]}
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/'data.zip';out=Path(d)/'prepared'
            with zipfile.ZipFile(archive,'w') as z:
                for split,data in [('train',train),('test',test)]:
                    z.writestr(f'WebQSP/data/WebQSP.{split}.json',json.dumps(data))
                    z.writestr(f'WebQSP/data/WebQSP.{split}.partial.json',json.dumps({'Questions':[]}))
            m=prepare(archive,out)
            inputs=(out/'inputs.jsonl').read_text()
            self.assertNotIn('SECRET',inputs)
            self.assertIn('SECRET',(out/'evaluation-only.jsonl').read_text())
            self.assertTrue(any('a' in ids and 'b' in ids for ids in m['splits'].values()))
            self.assertEqual(m['splits']['test'],['d'])


if __name__=='__main__':unittest.main()
