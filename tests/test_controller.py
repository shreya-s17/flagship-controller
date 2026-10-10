import unittest
from flagship_controller.controller import Edge, Graph, run, verify_path
from flagship_controller.examples import cases


class ControllerTests(unittest.TestCase):
    def test_grounded_answer(self):
        graph, query, budget = cases()["supported"]
        result = run(graph, query, max_expansions=budget)
        self.assertEqual(result["answer"], "university")
        self.assertTrue(verify_path(graph, query, graph.edges)["complete"])

    def test_missing_conflict_budget_abstain(self):
        for name in ("missing", "contradiction", "budget"):
            with self.subTest(name=name):
                graph, query, budget = cases()[name]
                result = run(graph, query, max_expansions=budget)
                self.assertEqual(result["terminal"], "ABSTAIN")
                self.assertLessEqual(result["trace"][-1]["cost"]["expansions_total"], budget)

    def test_wrong_branch_recovery_and_cost(self):
        graph, query, budget = cases()["recovery"]
        adaptive = run(graph, query, max_expansions=budget)
        fixed = run(graph, query, adaptive=False, max_expansions=budget)
        self.assertEqual(adaptive["answer"], "university")
        self.assertEqual(fixed["answer"], "university")
        self.assertTrue(any(s["reason"] == "constraint_failure" for s in adaptive["trace"]))
        self.assertLess(adaptive["trace"][-1]["cost"]["expansions_total"],
                        fixed["trace"][-1]["cost"]["expansions_total"])

    def test_provenance_required(self):
        graph, query, _ = cases()["supported"]
        graph.edges[0] = Edge("researcher", "supervisor", "mentor", "")
        self.assertEqual(run(graph, query)["terminal"], "ABSTAIN")

    def test_budget_zero_and_invalid_budget(self):
        graph, query, _ = cases()["supported"]
        result = run(graph, query, max_expansions=0)
        self.assertEqual(result["terminal"], "ABSTAIN")
        self.assertEqual(result["trace"][-1]["cost"]["expansions_total"], 0)
        with self.assertRaises(ValueError):
            run(graph, query, max_expansions=-1)

    def test_complete_path_already_retrieved_at_budget_can_answer(self):
        graph, query, _ = cases()["supported"]
        self.assertEqual(run(graph, query, max_expansions=2)["terminal"], "ANSWER")

    def test_repeatability_excluding_wall_time(self):
        graph, query, _ = cases()["recovery"]
        first, second = run(graph, query), run(graph, query)
        for result in (first, second):
            for step in result["trace"]:
                step["cost"].pop("elapsed_seconds")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
