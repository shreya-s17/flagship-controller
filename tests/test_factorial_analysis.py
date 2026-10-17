import unittest
from flagship_controller.factorial_analysis import known_total


class PhysicalAccountingTests(unittest.TestCase):
    def test_unknown_attempt_is_lower_bound_not_measured_zero(self):
        self.assertEqual(known_total([2, None, 0]), {'known_lower_bound': 2, 'complete': False, 'unknown_components': 1})
        self.assertEqual(known_total([2, 0]), {'known_lower_bound': 2, 'complete': True, 'unknown_components': 0})


if __name__ == '__main__':
    unittest.main()
