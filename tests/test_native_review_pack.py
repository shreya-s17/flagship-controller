import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from flagship_controller.native_review_pack import prepare,NATIVE_DIMENSIONS
from flagship_controller.review_assessment import validate
from flagship_controller.review_delivery import export


class NativeReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.study=self.root/'study';self.study.mkdir()
        inputs=b'{"id":"q","question":"What is Example?","split":"pilot"}\n'
        (self.study/'inputs.jsonl').write_bytes(inputs)
        self.order=[{'id':'q','variant':'tog-fixture'},{'id':'q','variant':'tog-other'}]
        (self.study/'manifest.json').write_text(json.dumps({'order':self.order,'input_sha256':hashlib.sha256(inputs).hexdigest()}))
        (self.study/'completion.json').write_text('{"completed":2}')
        rows=[{**item,'trace':[],'terminal':'ABSTAIN','answers':[],
            'native_response':'{Yes}. Example. Additional unobserved claim.' if i==0 else None,
            'observed_edges':[],'graph_audit':[],'gold':['SECRET'],'f1':1,
            'model_audit':[{'critique':'SECRET'}]} for i,item in enumerate(self.order)]
        (self.study/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.output=self.root/'pack'

    def test_missing_and_unmapped_native_outcomes_are_retained_without_scores(self):
        result=prepare([self.study],self.output)
        self.assertEqual(result['cases'],2)
        raw=(self.output/'reviewer/cases.jsonl').read_text()
        cases=list(map(json.loads,raw.splitlines()))
        self.assertEqual(sum(c['native_response'] is None for c in cases),1)
        self.assertIn('Additional unobserved claim.',raw)
        self.assertNotIn('SECRET',raw)
        for case in cases:
            self.assertNotIn('variant',case);self.assertNotIn('f1',case)
        self.assertEqual((self.output/'owner-key.json').stat().st_mode&0o777,0o600)
        template=json.loads((self.output/'reviewer/submission-template.json').read_text())
        self.assertEqual(set(template['judgments'][0]['dimensions']),set(NATIVE_DIMENSIONS))
        with self.assertRaises(ValueError):validate(self.output/'reviewer/cases.jsonl',template,NATIVE_DIMENSIONS)
        delivery=export(self.output/'reviewer',self.output/'reviewer/README.txt',self.root/'delivery.zip',result['cases_sha256'],NATIVE_DIMENSIONS)
        self.assertEqual(delivery['cases'],2)

    def test_incomplete_or_tampered_study_never_produces_review_directory(self):
        (self.study/'completion.json').write_text('{"completed":1}')
        with self.assertRaisesRegex(ValueError,'Completion'):prepare([self.study],self.output)
        self.assertFalse(self.output.exists())
        (self.study/'completion.json').write_text('{"completed":2}')
        (self.study/'inputs.jsonl').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'hash'):prepare([self.study],self.output)
        self.assertFalse(self.output.exists())

    def test_native_assessment_requires_projection_dimension_too(self):
        prepare([self.study],self.output)
        path=self.output/'reviewer/cases.jsonl'
        form=json.loads((self.output/'reviewer/submission-template.json').read_text())
        form.update(reviewer_id='fixture-only',qualification_statement='Synthetic test',
            independence_statement='Synthetic test',independence_attested=True,completed_at='2026-10-16T00:00:00Z')
        for item in form['judgments']:
            for value in item['dimensions'].values():value['reason']='Synthetic explicit unknown, not a real judgment'
        self.assertEqual(len(validate(path,form,NATIVE_DIMENSIONS)),2)
        del form['judgments'][0]['dimensions']['projection_faithfulness']
        with self.assertRaisesRegex(ValueError,'dimension'):validate(path,form,NATIVE_DIMENSIONS)

if __name__=='__main__':unittest.main()
