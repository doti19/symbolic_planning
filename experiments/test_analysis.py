import contextlib
import csv
import io
from pathlib import Path
import tempfile
import unittest

import analyze_results as analysis
from benchmark import FIELDS


def measurement(objective, run=1, **changes):
    row = dict(scenario="two-object-retrieval", objective=objective, run=run,
               status="solved", plan_length=2, planner_cost=2, weighted_cost=10,
               search_time_s=0.001 * run, total_runtime_s=0.1 * run, expanded_states=3)
    row.update(changes)
    return row


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.input = self.root / "benchmark.csv"

    def write_csv(self, rows, fields=FIELDS):
        with self.input.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def test_read_subset_with_out_of_order_rows(self):
        rows = [measurement(objective, run) for run in (3, 1, 2) for objective in ("weighted", "unit")]
        self.write_csv(rows)
        actual = analysis.read_runs(self.input, expected_repetitions=3)
        self.assertEqual(len(actual), 6)
        self.assertEqual(actual[0]["plan_length"], 2)
        self.assertEqual(actual[0]["search_time_s"], 0.003)
        self.assertEqual(actual[0]["scenario"], "two-object-retrieval")

    def test_pairwise_reductions_and_differences_precede_median(self):
        rows = []
        for run, unit_cost, weighted_cost, unit_actions, weighted_actions in (
            (1, 10, 5, 2, 3), (2, 100, 90, 10, 12), (3, 20, 0, 4, 7),
        ):
            rows.extend([
                measurement("unit", run, weighted_cost=unit_cost, plan_length=unit_actions,
                            planner_cost=unit_actions),
                measurement("weighted", run, weighted_cost=weighted_cost, plan_length=weighted_actions,
                            planner_cost=weighted_cost, expanded_states=9),
            ])
        self.write_csv(rows)
        summaries, warnings = analysis.summarize(analysis.read_runs(self.input))
        summary, = summaries
        self.assertEqual(warnings, [])
        self.assertEqual(summary["repetitions"], 3)
        self.assertEqual(summary["unit_actions"], 4)
        self.assertEqual(summary["weighted_actions"], 7)
        self.assertEqual(summary["unit_planner_cost"], 4)
        self.assertEqual(summary["weighted_planner_cost"], 5)
        self.assertEqual(summary["unit_weighted_cost"], 20)
        self.assertEqual(summary["optimal_weighted_cost"], 5)
        self.assertEqual(summary["plan_length_difference"], 2)
        self.assertEqual(summary["cost_reduction_percent"], 50)
        self.assertEqual(summary["cost_reduction_pairs"], 3)
        self.assertEqual(summary["unit_expanded_states"], 3)
        self.assertEqual(summary["weighted_expanded_states"], 9)
        self.assertEqual(summary["unit_search_time_s"], 0.002)
        self.assertAlmostEqual(summary["weighted_total_runtime_s"], 0.2)

    def test_zero_baseline_is_undefined_and_counted(self):
        self.write_csv([measurement(objective, weighted_cost=0) for objective in ("unit", "weighted")])
        summaries, warnings = analysis.summarize(analysis.read_runs(self.input))
        self.assertIsNone(summaries[0]["cost_reduction_percent"])
        self.assertEqual(summaries[0]["cost_reduction_pairs"], 0)
        self.assertIn("0/1 pairs", warnings[0])

    def test_partial_zero_baseline_keeps_defined_pair_count(self):
        self.write_csv([
            measurement("unit", 1, weighted_cost=0), measurement("weighted", 1, weighted_cost=0),
            measurement("unit", 2, weighted_cost=30), measurement("weighted", 2, weighted_cost=25),
        ])
        summaries, warnings = analysis.summarize(analysis.read_runs(self.input))
        self.assertAlmostEqual(summaries[0]["cost_reduction_percent"], 100 / 6)
        self.assertEqual(summaries[0]["cost_reduction_pairs"], 1)
        self.assertIn("1/2 pairs", warnings[0])

    def test_missing_and_duplicate_columns(self):
        for fields, message in (
            (tuple(field for field in FIELDS if field != "weighted_cost"), "missing required CSV columns"),
            ((*FIELDS, "run"), "duplicate CSV column names"),
        ):
            with self.subTest(fields=fields):
                self.write_csv([], fields)
                with self.assertRaisesRegex(ValueError, message):
                    analysis.read_runs(self.input)

    def test_invalid_measurements(self):
        for field, value in (
            ("plan_length", -1), ("plan_length", "2.5"), ("planner_cost", -1),
            ("weighted_cost", "NaN"), ("weighted_cost", ""), ("weighted_cost", -2),
            ("expanded_states", "inf"), ("search_time_s", -0.1), ("total_runtime_s", "nan"),
            ("run", 0), ("run", "one"),
        ):
            with self.subTest(field=field, value=value):
                row = measurement("unit")
                row[field] = value
                self.write_csv([row, measurement("weighted")])
                with self.assertRaisesRegex(ValueError, f"invalid {field} value"):
                    analysis.read_runs(self.input)

    def test_failed_planner_runs_are_rejected(self):
        for status in ("unsolvable", "timeout", "error", ""):
            with self.subTest(status=status):
                self.write_csv([measurement("unit", status=status), measurement("weighted")])
                with self.assertRaisesRegex(ValueError, "every row must be solved"):
                    analysis.read_runs(self.input)

    def test_duplicate_and_incomplete_pairs(self):
        for rows, message in (
            ([measurement("unit"), measurement("unit")], "duplicate scenario/objective/run"),
            ([measurement("unit")], "incomplete unit/weighted"),
            ([measurement("unit"), measurement("weighted", 2)], "incomplete unit/weighted"),
            ([measurement(obj, run) for obj in ("unit", "weighted") for run in (1, 3)],
             "repetitions must be complete"),
        ):
            with self.subTest(message=message):
                self.write_csv(rows)
                with self.assertRaisesRegex(ValueError, message):
                    analysis.read_runs(self.input)

    def test_expected_repetitions_detects_missing_final_pair(self):
        self.write_csv([measurement("unit"), measurement("weighted")])
        with self.assertRaisesRegex(ValueError, "1 through 3"):
            analysis.read_runs(self.input, expected_repetitions=3)

    def test_missing_optional_values_do_not_produce_partial_medians(self):
        self.write_csv([
            measurement("unit", 1, expanded_states="", search_time_s="", total_runtime_s=""),
            measurement("unit", 2), measurement("weighted", 1), measurement("weighted", 2),
        ])
        summaries, warnings = analysis.summarize(analysis.read_runs(self.input))
        for field in ("unit_expanded_states", "unit_search_time_s", "unit_total_runtime_s"):
            self.assertIsNone(summaries[0][field])
        self.assertEqual(len(warnings), 3)
        self.assertTrue(all("1/2 measurements" in warning for warning in warnings))
        self.assertEqual(summaries[0]["weighted_expanded_states"], 3)

    def test_empty_input_and_malformed_rows(self):
        for content, message in (
            (",".join(FIELDS) + "\n", "no benchmark runs"),
            (",".join(FIELDS) + "\na,b\n", "wrong number of CSV values"),
        ):
            with self.subTest(message=message):
                self.input.write_text(content)
                with self.assertRaisesRegex(ValueError, message):
                    analysis.read_runs(self.input)

    def test_invalid_input_generates_no_output(self):
        self.write_csv([measurement("unit", status="error"), measurement("weighted")])
        output = self.root / "figures"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
            analysis.main(["--input", str(self.input), "--output", str(output)])
        self.assertEqual(failure.exception.code, 2)
        self.assertFalse(output.exists())

    def test_generate_all_outputs_with_missing_metrics(self):
        from PIL import Image

        self.write_csv([measurement("unit", expanded_states="", search_time_s=""),
                        measurement("weighted", weighted_cost=8)])
        output = self.root / "figures"
        summary = self.root / "summary.csv"
        report = self.root / "analysis.md"
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr:
            result = analysis.main([
                "--input", str(self.input), "--output", str(output),
                "--summary", str(summary), "--report", str(report),
            ])
        self.assertEqual(result, 0)
        for stem in ("weighted_cost_comparison", "plan_length_comparison", "expanded_states_comparison"):
            self.assertTrue((output / f"{stem}.pdf").read_bytes().startswith(b"%PDF-"))
            with Image.open(output / f"{stem}.png") as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size[0], 1050)
                self.assertAlmostEqual(image.info["dpi"][0], 300, delta=0.1)
                image.verify()
        with summary.open(newline="") as stream:
            row, = list(csv.DictReader(stream))
        self.assertEqual(row["unit_expanded_states"], "")
        self.assertEqual(row["cost_reduction_percent"], "20.0")
        self.assertIn("20.00%", stdout.getvalue())
        self.assertIn("0/1 measurements", stderr.getvalue())
        self.assertIn("Measurement availability", report.read_text())


if __name__ == "__main__":
    unittest.main()
