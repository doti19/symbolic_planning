#!/usr/bin/env python3
"""Validate paired benchmark measurements and write summaries and paper figures."""

import argparse
import csv
import math
from pathlib import Path
from statistics import median
import sys

from benchmark import FIELDS, SCENARIOS, cost_reduction


HERE = Path(__file__).resolve().parent
OBJECTIVES = ("unit", "weighted")
OPTIONAL_METRICS = ("expanded_states", "search_time_s", "total_runtime_s")
INTEGER_METRICS = ("plan_length", "planner_cost", "weighted_cost", "expanded_states")
MEDIAN_FIELDS = {
    "plan_length": "actions",
    "planner_cost": "planner_cost",
    "weighted_cost": "weighted_cost",
    "expanded_states": "expanded_states",
    "search_time_s": "search_time_s",
    "total_runtime_s": "total_runtime_s",
}
SUMMARY_FIELDS = (
    "scenario", "repetitions", "unit_actions", "weighted_actions",
    "plan_length_difference", "unit_planner_cost", "weighted_planner_cost",
    "unit_weighted_cost", "optimal_weighted_cost", "cost_reduction_percent",
    "cost_reduction_pairs", "unit_expanded_states", "weighted_expanded_states",
    "unit_search_time_s", "weighted_search_time_s",
    "unit_total_runtime_s", "weighted_total_runtime_s",
)
SCENARIO_NAMES = {
    "cost-nav": "Five-room\nnavigation",
    "eight-room": "Eight-room\nnavigation",
    "door-detour": "Door vs.\ndetour",
    "object-retrieval": "Object\nretrieval",
    "two-object-retrieval": "Two-object\nretrieval",
}


def read_runs(path, expected_repetitions=None):
    """Require solved, unique, consecutively numbered pairs before any output."""
    if expected_repetitions is not None and expected_repetitions < 1:
        raise ValueError("expected repetitions must be positive")
    runs = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        missing = sorted(set(FIELDS) - set(fields))
        if missing:
            raise ValueError(f"missing required CSV columns: {', '.join(missing)}")
        if len(fields) != len(set(fields)):
            raise ValueError("duplicate CSV column names")
        for row in reader:
            location = f"line {reader.line_num}"
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{location}: wrong number of CSV values")
            row = {key: value.strip() for key, value in row.items()}
            if not row["scenario"] or row["objective"] not in OBJECTIVES:
                raise ValueError(f"{location}: scenario is required and objective must be unit or weighted")
            if row["status"] != "solved":
                raise ValueError(f"{location}: {row['scenario']} {row['objective']} run {row['run']} "
                                 f"has status {row['status']!r}; every row must be solved")
            for field in ("run", *MEDIAN_FIELDS):
                value = row[field]
                if value == "" and field in OPTIONAL_METRICS:
                    row[field] = None
                    continue
                convert = int if field == "run" or field in INTEGER_METRICS else float
                try:
                    number = convert(value)
                    if not math.isfinite(number) or number < 0 or (field == "run" and number == 0):
                        raise ValueError
                except (ValueError, OverflowError):
                    raise ValueError(f"{location}: invalid {field} value {value!r}") from None
                row[field] = number
            key = (row["scenario"], row["objective"], row["run"])
            if key in runs:
                raise ValueError(f"{location}: duplicate scenario/objective/run {key}")
            runs[key] = row
    if not runs:
        raise ValueError("CSV contains no benchmark runs")

    for scenario in {key[0] for key in runs}:
        numbers = {objective: {run for name, obj, run in runs
                               if name == scenario and obj == objective}
                   for objective in OBJECTIVES}
        if not numbers["unit"] or numbers["unit"] != numbers["weighted"]:
            raise ValueError(f"{scenario}: incomplete unit/weighted repetition pairs")
        # A CSV alone cannot reveal a final repetition missing from both objectives.
        count = expected_repetitions if expected_repetitions is not None else len(numbers["unit"])
        if numbers["unit"] != set(range(1, count + 1)):
            raise ValueError(f"{scenario}: repetitions must be complete from 1 through {count}")
    return list(runs.values())


def summarize(runs):
    """Use all repetitions for group medians and matched runs for differences."""
    scenarios = {row["scenario"] for row in runs}
    order = [name for name in SCENARIOS if name in scenarios] + sorted(scenarios - set(SCENARIOS))
    summaries = []
    warnings = []
    for scenario in order:
        groups = {objective: sorted(
            (row for row in runs if row["scenario"] == scenario and row["objective"] == objective),
            key=lambda row: row["run"],
        ) for objective in OBJECTIVES}
        pairs = list(zip(groups["unit"], groups["weighted"]))
        summary = {"scenario": scenario, "repetitions": len(pairs)}
        for objective, rows in groups.items():
            for source, target in MEDIAN_FIELDS.items():
                values = [row[source] for row in rows if row[source] is not None]
                summary[f"{objective}_{target}"] = median(values) if len(values) == len(rows) else None
                if len(values) != len(rows):
                    warnings.append(f"{scenario} {objective}: {source} has {len(values)}/{len(rows)} "
                                    "measurements; its median is unavailable")
        summary["optimal_weighted_cost"] = summary.pop("weighted_weighted_cost")
        reductions = [cost_reduction(unit["weighted_cost"], weighted["weighted_cost"])
                      for unit, weighted in pairs if unit["weighted_cost"] != 0]
        summary["cost_reduction_percent"] = median(reductions) if reductions else None
        summary["cost_reduction_pairs"] = len(reductions)
        summary["plan_length_difference"] = median(
            weighted["plan_length"] - unit["plan_length"] for unit, weighted in pairs
        )
        if len(reductions) != len(pairs):
            warnings.append(f"{scenario}: cost reduction is defined for {len(reductions)}/{len(pairs)} "
                            "pairs because a zero unit weighted cost has no percentage reduction")
        summaries.append(summary)
    return summaries, warnings


def display(value):
    return "n/a" if value is None else f"{value:g}"


def write_figures(summaries, output):
    # Keep CSV processing and aggregation usable without the plotting dependency.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    charts = (
        ("weighted_cost_comparison", "unit_weighted_cost", "optimal_weighted_cost", "Total weighted action cost"),
        ("plan_length_comparison", "unit_actions", "weighted_actions", "Number of actions"),
        ("expanded_states_comparison", "unit_expanded_states", "weighted_expanded_states", "Expanded states"),
    )
    style = {
        "font.family": "DejaVu Sans", "font.size": 7.5,
        "axes.labelsize": 8, "xtick.labelsize": 6.5, "ytick.labelsize": 7,
        "legend.fontsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
    }
    with plt.rc_context(style):
        for filename, unit_field, weighted_field, ylabel in charts:
            figure, axis = plt.subplots(figsize=(3.5, 2.6), layout="constrained")
            positions = range(len(summaries))
            for field, label, offset, color, hatch in (
                (unit_field, "Unit-cost planning", -0.19, "#0072B2", ""),
                (weighted_field, "Weighted-cost planning", 0.19, "#E69F00", "//"),
            ):
                values = [row[field] for row in summaries]
                centers = [position + offset for position in positions]
                bars = axis.bar(centers, [math.nan if value is None else value for value in values],
                                width=0.36, label=label, color=color, edgecolor="#333333",
                                linewidth=0.5, hatch=hatch)
                for bar, value, center in zip(bars, values, centers):
                    axis.annotate(display(value), (center, 0 if value is None else bar.get_height()),
                                  xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                                  fontsize=7)
            maximum = max((row[field] for row in summaries for field in (unit_field, weighted_field)
                           if row[field] is not None), default=0)
            axis.set_ylim(0, max(1, maximum * 1.25))
            axis.set_xticks(list(positions), [SCENARIO_NAMES.get(row["scenario"], row["scenario"].replace("-", "\n"))
                                             for row in summaries])
            axis.set_xlabel("Scenario")
            axis.set_ylabel(ylabel)
            axis.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
            axis.set_axisbelow(True)
            axis.grid(axis="y", color="#dddddd", linewidth=0.5)
            axis.tick_params(axis="x", length=0, pad=5)
            axis.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
                        frameon=False, handlelength=1.3, columnspacing=1)
            try:
                figure.savefig(output / f"{filename}.pdf")
                figure.savefig(output / f"{filename}.png", dpi=300)
            finally:
                plt.close(figure)


def write_report(summaries, warnings, input_path, report):
    total = sum(2 * row["repetitions"] for row in summaries)
    repetitions = ", ".join(str(n) for n in sorted({row["repetitions"] for row in summaries}))
    lines = [
        "# Experimental results analysis", "", "## Experimental setup", "",
        f"The input `{input_path.name}` contains {total} solved runs across {len(summaries)} scenarios, "
        f"with {repetitions} repetitions per objective. The robot benchmark uses Fast Downward 26.6 "
        "with `astar(lmcut())` for both objectives. The input CSV stores measurements. Planner "
        "configuration and provenance for the saved snapshot are documented in "
        "[the evidence guide](evidence/README.md).", "",
        "Unit-cost planning minimizes action count. Both resulting plans are evaluated with the "
        "weighted problem's directed movement distances, door-opening costs, and unit manipulation "
        "costs. Each objective's metrics are medians over all its repetitions. Cost reduction and "
        "action-count difference are computed within matched repetition numbers and then summarized "
        "by their medians. Zero-cost baselines have undefined percentage reductions.", "",
        "## Results", "",
        "| Scenario | Pairs | Unit actions | Weighted actions | Unit plan weighted cost | Weighted plan weighted cost | Reduction (%) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summaries:
        reduction = row["cost_reduction_percent"]
        lines.append(f"| {row['scenario']} | {row['repetitions']} | {display(row['unit_actions'])} | "
                     f"{display(row['weighted_actions'])} | {display(row['unit_weighted_cost'])} | "
                     f"{display(row['optimal_weighted_cost'])} | "
                     f"{'n/a' if reduction is None else f'{reduction:.2f}'} |")
    lines.extend(["", "The figures show median weighted cost, action count, and expanded states. "
                  "Expanded states measure planning search effort. Weighted action cost measures "
                  "the modeled execution objective.", "", "## Discussion", ""])
    discussion = {
        "cost-nav": "The five-room model offers a two-step route through the lab and a longer route "
                    "through the hallway and office. Their movement costs can favor the longer route.",
        "eight-room": "The eight-room model also offers a route through the library and classroom, "
                      "whose low movement costs can offset additional actions.",
        "door-detour": "The service-door shortcut requires a costly opening action. The weighted "
                       "objective balances that cost against traveling around the door.",
        "object-retrieval": "Object retrieval includes both the outward and return journey and a "
                            "handover. A door-opening cost is paid once, which can make the shortcut "
                            "worth using for a round trip under both objectives.",
        "two-object-retrieval": "Retrieving two objects combines route selection with pickup and "
                                "delivery order. Additional movement actions can replace an expensive "
                                "door opening and reduce accumulated weighted cost.",
    }
    for row in summaries:
        scenario = row["scenario"]
        if scenario in discussion:
            lines.append(f"- **{scenario}**. {discussion[scenario]} The observed median paired "
                         f"action-count difference is {row['plan_length_difference']:+g}, "
                         f"with weighted costs of {display(row['unit_weighted_cost'])} and "
                         f"{display(row['optimal_weighted_cost'])} for unit and weighted planning.")
    lines.extend(["", "## Limitations", "",
                  "These are small, manually designed building environments with synthetic action "
                  f"costs. The {repetitions} repetitions per objective across these deterministic tasks restrict "
                  "generalization to larger or real-world robotic environments. Repetitions measure "
                  "repeatability on each task and do not provide independent problem instances. "
                  "No significance tests are performed.", "",
                  "Planning times are extremely short in the saved benchmark. Search time comes from "
                  "the planner's `Search time:` measurement, while total runtime includes translation "
                  "and process overhead. Tiny differences cannot establish a runtime advantage. "
                  "The previously reported benchmark had no independent VAL plan validation. "
                  "Modeled cost reductions do not establish physical energy savings.", ""])
    if warnings:
        lines.extend(["## Measurement availability", "", *[f"- {warning}." for warning in warnings], ""])
    report.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "results" / "benchmark.csv")
    parser.add_argument("--output", type=Path, default=HERE / "figures", help="directory for PDF and PNG figures")
    parser.add_argument("--summary", type=Path, default=HERE / "results" / "summary.csv")
    parser.add_argument("--report", type=Path, default=HERE / "RESULTS_ANALYSIS.md")
    parser.add_argument("--expected-repetitions", type=int, help="require this many pairs in every scenario")
    args = parser.parse_args(argv)
    try:
        if len({path.resolve() for path in (args.input, args.summary, args.report)}) != 3:
            raise ValueError("input, summary, and report paths must be distinct")
        summaries, warnings = summarize(read_runs(args.input, args.expected_repetitions))
        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        args.output.mkdir(parents=True, exist_ok=True)
        write_figures(summaries, args.output)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
            writer.writeheader()
            writer.writerows(summaries)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        write_report(summaries, warnings, args.input, args.report)
    except ImportError as exc:
        parser.error(f"plotting dependency unavailable ({exc}); install experiments/requirements-analysis.txt")
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    print(f"{'Scenario':<23} {'Pairs':>5} {'Actions U/W':>13} {'Weighted cost U/W':>18} {'Reduction':>10}")
    for row in summaries:
        actions = f"{display(row['unit_actions'])}/{display(row['weighted_actions'])}"
        costs = f"{display(row['unit_weighted_cost'])}/{display(row['optimal_weighted_cost'])}"
        reduction = row["cost_reduction_percent"]
        percent = "n/a" if reduction is None else f"{reduction:.2f}%"
        print(f"{row['scenario']:<23} {row['repetitions']:>5} {actions:>13} {costs:>18} {percent:>10}")
    print(f"Summary: {args.summary}\nFigures: {args.output}\nReport: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
