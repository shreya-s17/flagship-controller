import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from flagship_controller.review_delivery import export
from flagship_controller.review_pack import DIMENSIONS


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.reviewer=self.root/'reviewer';self.reviewer.mkdir()
        self.cases=b'{"case_id":"fixture"}\n';self.digest=hashlib.sha256(self.cases).hexdigest()
        (self.reviewer/'cases.jsonl').write_bytes(self.cases)
        (self.reviewer/'README.txt').write_text('Instructions')
        self.form={'cases_sha256':self.digest,'independence_attested':False,'reviewer_id':'',
            'judgments':[{'case_id':'fixture','dimensions':{d:{'label':'unknown','reason':''} for d in DIMENSIONS}}]}
        self.template=self.reviewer/'submission-template.json';self.template.write_text(json.dumps(self.form))
        self.brief=self.root/'BRIEF.txt';self.brief.write_text('Brief')
        self.out=self.root/'delivery.zip'

    def test_only_allowlisted_files_are_delivered_and_read_back(self):
        (self.root/'owner-key.json').write_text('SECRET')
        (self.reviewer/'gold.json').write_text('SECRET')
        result=export(self.reviewer,self.brief,self.out,self.digest)
        self.assertEqual(result['cases'],1)
        with zipfile.ZipFile(self.out) as archive:
            self.assertEqual(len(archive.namelist()),5)
            self.assertEqual(archive.read('cases.jsonl'),self.cases)
            self.assertNotIn('SECRET',str([archive.read(n) for n in archive.namelist()]))
        with self.assertRaisesRegex(ValueError,'existing'):export(self.reviewer,self.brief,self.out,self.digest)

    def test_pack_hash_and_template_mismatch_fail_before_archive_creation(self):
        with self.assertRaisesRegex(ValueError,'hash'):export(self.reviewer,self.brief,self.out,'bad')
        self.assertFalse(self.out.exists())
        self.form['judgments'][0]['case_id']='other';self.template.write_text(json.dumps(self.form))
        with self.assertRaisesRegex(ValueError,'order'):export(self.reviewer,self.brief,self.out,self.digest)
        self.assertFalse(self.out.exists())

    def test_completed_review_or_identity_is_never_sent_as_blank(self):
        self.form['reviewer_id']='Private reviewer';self.template.write_text(json.dumps(self.form))
        with self.assertRaisesRegex(ValueError,'identity'):export(self.reviewer,self.brief,self.out,self.digest)
        self.assertFalse(self.out.exists())

if __name__=='__main__': unittest.main()
