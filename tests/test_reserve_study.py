from pathlib import Path
import json
import tempfile
import unittest
from flagship_controller.reserve_study import reserve


class ReservationTests(unittest.TestCase):
    def test_training_only_no_exact_cross_group_overlap_and_stable_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);records=[{'id':'dev','question':'Where is Example?','split':'pilot'},
                {'id':'duplicate','question':'where is example','split':'train_remaining'},
                {'id':'test','question':'Test question','split':'test'},
                {'id':'a','question':'Eligible A','split':'train_remaining'},
                {'id':'b','question':'Eligible B','split':'train_remaining'}]
            source=root/'input';source.write_text(''.join(json.dumps(r)+'\n' for r in records))
            first=reserve(source,root/'one',2)
            self.assertEqual(set(first['question_ids']),{'a','b'});self.assertFalse(first['gold_read'])
            source.write_text(''.join(json.dumps(r)+'\n' for r in reversed(records)))
            second=reserve(source,root/'two',2)
            self.assertEqual(first['question_ids'],second['question_ids'])
            with self.assertRaises(ValueError):reserve(source,root/'one',2)
            records[0]['parses']=[];source.write_text(json.dumps(records[0]))
            with self.assertRaisesRegex(ValueError,'Question-only'):reserve(source,root/'three',1)

    def test_near_development_exclusion_precedes_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);records=[{'id':'dev','question':'What films did Example appear in?','split':'pilot'},
                {'id':'near','question':'What movies did Example appear in?','split':'train_remaining'},
                {'id':'different','question':'Which currency is used in Exampleland?','split':'train_remaining'}]
            source=root/'input';source.write_text(''.join(json.dumps(r)+'\n' for r in records))
            result=reserve(source,root/'out',1,max_development_similarity=.85)
            self.assertEqual(result['question_ids'],['different'])
            self.assertFalse(result['near_text_flags'])
            with self.assertRaisesRegex(ValueError,'Insufficient'):
                reserve(source,root/'insufficient',2,max_development_similarity=.85)
