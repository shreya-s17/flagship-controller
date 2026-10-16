import unittest
from flagship_controller.declared_json_tog_adapter import select_declared
from flagship_controller.webqsp_runtime import Blocked


class DeclaredJsonTests(unittest.TestCase):
    candidates=[{'entity':'m.mx','names':['Mexico']},{'entity':'m.peso','names':['Mexican peso']}]
    def test_explicit_declared_indices_map_every_answer_without_prose_extraction(self):
        self.assertEqual(select_declared({'decision':'ANSWER','answer_indices':[0]},self.candidates),['m.mx'])
        self.assertEqual(select_declared({'decision':'CONTINUE','answer_indices':[]},self.candidates),[])

    def test_invalid_indices_and_inconsistent_stop_fail_closed(self):
        for value in ([True],[2],[-1],[0,0],[]):
            with self.assertRaises(Blocked):select_declared({'decision':'ANSWER','answer_indices':value},self.candidates)
        with self.assertRaisesRegex(Blocked,'inconsistent'):select_declared({'decision':'CONTINUE','answer_indices':[0]},self.candidates)
        with self.assertRaises(Blocked):select_declared({'decision':'MAYBE','answer_indices':[]},self.candidates)

if __name__=='__main__':unittest.main()
