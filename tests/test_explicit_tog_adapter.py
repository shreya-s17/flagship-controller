import unittest
from flagship_controller.explicit_tog_adapter import decode


class DeclaredAnswerTests(unittest.TestCase):
    names={'m.mx':['Mexico'],'m.peso':['Mexican peso'],'m.coin':['Old coin']}
    def test_context_and_question_mentions_never_select_ids(self):
        native='{Yes}. Mexican peso is in the question. The answer is Mexico.\nFINAL_ANSWER: ["Mexico"]'
        self.assertEqual(decode(native,self.names,'reasoning_yes')[0],['m.mx'])
        native='{Yes}. Old coin is historical context. Use Mexican peso.\nFINAL_ANSWER: ["Mexican peso"]'
        self.assertEqual(decode(native,self.names,'reasoning_yes')[0],['m.peso'])

    def test_missing_malformed_multiple_or_nonfinal_channel_abstains(self):
        for native in ('{Yes}. Mexico','{Yes}.\nFINAL_ANSWER: Mexico',
            'FINAL_ANSWER: ["Mexico"]\nFINAL_ANSWER: ["Mexico"]',
            'FINAL_ANSWER: ["Mexico"]\nExtra text', 'FINAL_ANSWER: {"name":"Mexico"}',
            'FINAL_ANSWER: [true]','FINAL_ANSWER: ["Mexico","MEXICO"]'):
            self.assertEqual(decode(native,self.names,'reasoning_yes')[0],[])

    def test_observed_names_cannot_resolve_shared_alias_or_invented_name(self):
        native='FINAL_ANSWER: ["Mexico"]'
        ambiguous={**self.names,'m.other':['Mexico']}
        self.assertEqual(decode(native,ambiguous,'reasoning_yes')[0],[])
        self.assertEqual(decode('FINAL_ANSWER: ["Mexican pesos"]',self.names,'reasoning_yes')[0],[])

    def test_parametric_fallback_and_no_reasoning_cannot_be_admitted(self):
        for stop in ('half_stop','depth_direct_fallback','reasoning_no',None):
            self.assertEqual(decode('FINAL_ANSWER: ["Mexico"]',self.names,stop)[0],[])

    def test_explicit_multiple_answers_map_all_or_abstain(self):
        self.assertEqual(decode('FINAL_ANSWER: ["Mexico", "Mexican peso"]',self.names,'reasoning_yes')[0],['m.mx','m.peso'])
        self.assertEqual(decode('FINAL_ANSWER: ["Mexico", "Unknown"]',self.names,'reasoning_yes')[0],[])

if __name__=='__main__':unittest.main()
