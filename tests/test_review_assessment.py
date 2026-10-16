import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from flagship_controller.review_assessment import validate,assess,agreement,DIMENSIONS


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.pack=Path(self.directory.name)/'cases.jsonl'
        self.pack.write_text(json.dumps({'case_id':'fixture'})+'\n')
        self.review={'reviewer_id':'fixture-one','qualification_statement':'Fixture only, not real reviewer',
            'independence_statement':'Fixture only','independence_attested':True,'completed_at':'2026-10-16T00:00:00Z',
            'cases_sha256':hashlib.sha256(self.pack.read_bytes()).hexdigest(),
            'judgments':[{'case_id':'fixture','dimensions':{d:{'label':'unknown','reason':'Synthetic test of explicit unknown'} for d in DIMENSIONS}}]}

    def test_blank_defaults_are_not_completed_reviews(self):
        with self.assertRaises(ValueError):validate(self.pack,{'review':{d:'unknown' for d in DIMENSIONS}})
        r=copy.deepcopy(self.review);r['judgments'][0]['dimensions']['anchor_identity']['reason']=''
        with self.assertRaisesRegex(ValueError,'written reason'):validate(self.pack,r)

    def test_pack_identity_and_attestation_required(self):
        for key,value in [('cases_sha256','wrong'),('independence_attested',False),('completed_at','2026-10-16')]:
            r={**self.review,key:value}
            with self.assertRaises(ValueError):validate(self.pack,r)

    def test_distinct_two_reviewers_and_complete_dimensions_required(self):
        for reviews in ([self.review],[self.review,self.review]):
            with self.assertRaises(ValueError):assess(self.pack,reviews)
        r=copy.deepcopy(self.review);del r['judgments'][0]['dimensions']['query_meaning']
        with self.assertRaisesRegex(ValueError,'dimension'):validate(self.pack,r)

    def test_unknown_agreement_is_not_perfect_certainty(self):
        result=agreement(['unknown'],['unknown'])
        self.assertEqual(result['raw_agreement'],1)
        self.assertIsNone(result['cohen_kappa']);self.assertIsNone(result['joint_known_agreement'])
        self.assertEqual(result['joint_known_n'],0)

    def test_disagreement_and_denominator(self):
        r=copy.deepcopy(self.review);r['reviewer_id']='fixture-two'
        r['judgments'][0]['dimensions']['query_meaning']['label']='contradicted'
        result=assess(self.pack,[self.review,r])
        self.assertEqual(len(result['disagreements_for_adjudication']),1)
        self.assertEqual(result['agreement']['query_meaning']['raw_agreement'],0)
        self.assertEqual(result['agreement']['query_meaning']['joint_known_n'],0)

if __name__=='__main__':unittest.main()
