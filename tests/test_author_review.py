import copy
import json
from pathlib import Path
import tempfile
import unittest
from flagship_controller import author_review, independent_review
from flagship_controller.review_pack import DIMENSIONS


class AuthorReviewTests(unittest.TestCase):
    def fixture(self, temp):
        study = Path(temp) / 'study';study.mkdir()
        (study / 'inputs.jsonl').write_text(json.dumps({'id': 'q', 'question': 'Who <script>alert(1)</script>?'}) + '\n')
        row = {'id': 'q', 'variant': 'fixture', 'terminal': 'ABSTAIN', 'answers': [], 'reason': 'fixture',
               'trace': [], 'graph_audit': [], 'cost': {}}
        (study / 'predictions.jsonl').write_text(json.dumps(row) + '\n')
        output = Path(temp) / 'review';author_review.prepare(study, output)
        pack = json.loads((output / 'cases.json').read_text())
        review = {'review_role': 'author', 'independence_attested': False, 'author_name': 'Test fixture only',
            'completed_at': '2026-10-17T10:00:00Z', 'source_predictions_sha256': pack['source_predictions_sha256'],
            'judgments': [{'case_id': 'A01', 'dimensions': {d: {'label': 'unknown', 'reason': 'Fixture evidence missing'} for d in DIMENSIONS}}]}
        return output, review

    def test_author_judgments_stay_separate_and_blank_forms_are_not_reviews(self):
        with tempfile.TemporaryDirectory() as temp:
            output, review = self.fixture(temp)
            result = author_review.validate(output / 'cases.json', review)
            self.assertEqual(result['reviewed_cases'], 1)
            self.assertEqual(result['independent_reviewers'], 0)
            with self.assertRaises(ValueError):author_review.validate(output / 'cases.json', {})
            review['judgments'][0]['dimensions']['query_meaning']['reason'] = ''
            with self.assertRaisesRegex(ValueError, 'written reason'):
                author_review.validate(output / 'cases.json', review)

    def test_untrusted_question_does_not_break_script_element(self):
        with tempfile.TemporaryDirectory() as temp:
            output, _ = self.fixture(temp)
            page = (output / 'author-review.html').read_text()
            self.assertNotIn('<script>alert(1)</script>', page)
            self.assertIn('\\u003cscript>', page)
            self.assertIn('textContent', page)

    def test_explicit_author_role_cannot_be_relabelled_by_attestation(self):
        with tempfile.TemporaryDirectory() as temp:
            output, review = self.fixture(temp);review['independence_attested'] = True
            with self.assertRaisesRegex(ValueError, 'cannot count as independent'):
                independent_review.validate(output / 'cases.json', review)
            with self.assertRaisesRegex(ValueError, 'non-independent'):
                author_review.validate(output / 'cases.json', review)


if __name__ == '__main__':unittest.main()
