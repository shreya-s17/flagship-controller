import unittest
from flagship_controller.official_score import prf,score

class OfficialScoreTests(unittest.TestCase):
    def test_empty_conventions(self):
        self.assertEqual(prf(['a'],[]),(1.,0.,0.));self.assertEqual(prf([],['a']),(0.,1.,0.))
        self.assertEqual(prf([],[]),(1.,1.,1.))
    def test_admitted_question_can_select_noncomplete_parse(self):
        good={'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},'Answers':[{'AnswerArgument':'a'}]}
        other={'AnnotatorComment':{'QuestionQuality':'Bad','ParseQuality':'Incomplete'},'Answers':[{'AnswerArgument':'b'}]}
        self.assertEqual(score([{'id':'q','terminal':'ANSWER','answers':['b']}],[{'id':'q','parses':[good,other]}])['macro_f1'],1.)
    def test_denominator_boundaries(self):
        with self.assertRaises(ValueError):score([], [{'id':'missing','parses':[]}])
        with self.assertRaises(ValueError):score([{'id':'q'},{'id':'q'}],[])
    def test_nonoverlap_numerical_convention(self):
        self.assertGreater(prf(['a'],['b'])[2],0.)
        self.assertAlmostEqual(prf(['a','b'],['b'])[2],2/3)
