import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

import benchmark


# Captured with Fast Downward 26.6 and astar(lmcut()) on the checked-in pair.
UNIT_PLAN = """\
(open-door service-door entrance storage)
(move entrance storage)
(pick-up book storage left)
(move storage meeting)
(move meeting office)
(pick-up laptop office right)
(move office hallway)
(move hallway entrance)
(hand-over book professor entrance left)
(hand-over laptop professor entrance right)
; cost = 10 (unit cost)
"""

WEIGHTED_PLAN = """\
(move entrance hallway)
(move hallway office)
(pick-up laptop office left)
(move office meeting)
(move meeting storage)
(pick-up book storage right)
(move storage classroom)
(move classroom library)
(move library hallway)
(move hallway entrance)
(hand-over book professor entrance right)
(hand-over laptop professor entrance left)
; cost = 25 (general cost)
"""


class LogTests(unittest.TestCase):
    def test_solved_log_metrics(self):
        log = """\
[t=0.001241s, 435307520 KB] Actual search time: 0.000236s
[t=0.001244s, 435307520 KB] Plan length: 10 step(s).
[t=0.001244s, 435307520 KB] Plan cost: 10
[t=0.001244s, 435307520 KB] Expanded 21 state(s).
[t=0.001244s, 435307520 KB] Expanded until last jump: 11 state(s).
[t=0.001244s, 435307520 KB] Search time: 0.000291s
[t=0.001244s, 435307520 KB] Total time: 0.001244s
search exit code: 0
"""
        self.assertEqual(benchmark.parse_log(log), {
            "plan_length": 10, "planner_cost": 10,
            "expanded_states": 21, "search_time_s": 0.000291,
        })

    def test_partial_unsolvable_log_preserves_zero_expansions(self):
        log = """\
[t=0.000797s, 435308048 KB] Search terminated -- no plan exists!
[t=0.000800s, 435308048 KB] Actual search time: 0.000004s
[t=0.000803s, 435308048 KB] Expanded 0 state(s).
Task is provably unsolvable.
search exit code: 11
"""
        self.assertEqual(benchmark.parse_log(log), {"expanded_states": 0})

    def test_exit_codes(self):
        for outcome, codes, status in (
            ("successful planning", (0,), "solved"),
            ("proven unsolvable", (10, 11), "unsolvable"),
            ("translator or search timeout", (21, 23), "timeout"),
            ("subprocess timeout", (None,), "timeout"),
            ("out of memory", (20, 22), "error"),
            ("incomplete or bounded search", (12, 13), "error"),
            ("portfolio resource outcome", (1, 2, 3, 24), "error"),
            ("other exit code", (31, 99, -9), "error"),
        ):
            for code in codes:
                with self.subTest(outcome=outcome, code=code):
                    self.assertEqual(benchmark.planner_status(code), status)


class WeightedCostTests(unittest.TestCase):
    def test_all_configured_pairs_match(self):
        for scenario in benchmark.SCENARIOS:
            with self.subTest(scenario=scenario):
                benchmark.load_pair(scenario)

    def test_movement_door_and_fixed_costs(self):
        _, costs = benchmark.load_pair("two-object-retrieval")
        for action, expected in (
            (("move", "entrance", "storage"), 2),
            (("open-door", "service-door", "entrance", "storage"), 12),
            (("open-cabinet", "cabinet", "storage"), 1),
        ):
            with self.subTest(action=action):
                self.assertEqual(benchmark.evaluate_plan([action], costs), expected)

    def test_missing_assignments_and_unknown_actions(self):
        with self.assertRaisesRegex(ValueError, "missing weighted assignment"):
            benchmark.evaluate_plan([("move", "storage", "entrance")], {
                ("distance", "entrance", "storage"): 2,
            })
        with self.assertRaisesRegex(ValueError, "missing weighted assignment"):
            benchmark.evaluate_plan([("open-door", "service-door", "entrance", "storage")], {})
        with self.assertRaisesRegex(ValueError, "unknown action"):
            benchmark.evaluate_plan([("close-door", "service-door")], {})

    def test_two_object_retrieval_regression(self):
        _, costs = benchmark.load_pair("two-object-retrieval")
        unit, unit_reported = benchmark.parse_plan(UNIT_PLAN)
        weighted, weighted_reported = benchmark.parse_plan(WEIGHTED_PLAN)
        self.assertEqual((len(unit), unit_reported), (10, 10))
        self.assertEqual((len(weighted), weighted_reported), (12, 25))

        unit_cost = benchmark.evaluate_plan(unit, costs)
        weighted_cost = benchmark.evaluate_plan(weighted, costs)
        self.assertEqual((unit_cost, weighted_cost), (30, 25))
        self.assertAlmostEqual(benchmark.cost_reduction(unit_cost, weighted_cost), 100 / 6)

    def test_empty_plan_and_zero_baseline(self):
        actions, reported = benchmark.parse_plan("; cost = 0 (unit cost)\n")
        self.assertEqual((actions, reported), ([], 0))
        self.assertEqual(benchmark.evaluate_plan(actions, {}), 0)
        self.assertIsNone(benchmark.cost_reduction(0, 0))
        self.assertEqual(benchmark.cost_reduction(5, 5), 0)


class TrialTests(unittest.TestCase):
    def test_wall_timeout_and_error_ignore_existing_plan(self):
        scenario = "two-object-retrieval"
        paths, costs = benchmark.load_pair(scenario)
        for ending, timeout, status, detail in (
            ("import time; time.sleep(30)", 1, "timeout", "wall-clock limit of 1s"),
            ("raise SystemExit(31)", 5, "error", "exit code 31"),
            ("raise SystemExit(2)", 5, "error", "portfolio found a plan and ran out of time"),
            ("raise SystemExit(11)", 5, "unsolvable", "search proved the task unsolvable"),
        ):
            with self.subTest(ending=ending), tempfile.TemporaryDirectory() as temporary:
                # The stand-in leaves a plan and a diagnostic before stopping or timing out.
                command = [sys.executable, "-c", (
                    f"from pathlib import Path; Path('sas_plan').write_text({UNIT_PLAN!r}); "
                    f"print('test diagnostic', flush=True); {ending}"
                )]
                evidence = Path(temporary) / "trial"
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    row = benchmark.run_trial(command, scenario, "unit", 1, paths["unit"],
                                              costs, timeout, evidence)
                self.assertEqual(row["status"], status)
                self.assertIn(detail, stderr.getvalue())
                self.assertGreater(row["total_runtime_s"], 0)
                self.assertIsNone(row.get("weighted_cost"))
                self.assertIsNone(row.get("plan_length"))
                self.assertEqual((evidence / "planner.log").read_text(), "test diagnostic\n")
                self.assertEqual((evidence / "sas_plan").read_text(), UNIT_PLAN)


if __name__ == "__main__":
    unittest.main()
