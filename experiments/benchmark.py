#!/usr/bin/env python3
"""Compare unit and weighted planning on the robot's paired PDDL problems."""

import argparse
import csv
import math
import os
from pathlib import Path
import re
import shutil
import signal
from statistics import median
import subprocess
import sys
import tempfile
from time import perf_counter


HERE = Path(__file__).resolve().parent
PDDL = HERE.parent / "pddl"
DOMAIN = PDDL / "domain-costs.pddl"
SCENARIOS = (
    "cost-nav",
    "eight-room",
    "door-detour",
    "object-retrieval",
    "two-object-retrieval",
)
SEARCH = "astar(lmcut())"
VERSION = "Fast Downward 26.6"
FIELDS = (
    "scenario", "objective", "run", "status", "plan_length", "planner_cost",
    "weighted_cost", "search_time_s", "total_runtime_s", "expanded_states",
)

# Parameter order and fixed costs come from pddl/domain-costs.pddl.
ACTION_ARITY = {
    "move": 2,
    "open-door": 3,
    "pick-up": 3,
    "put-on-table": 4,
    "hand-over": 4,
    "open-cabinet": 2,
    "take-from-cabinet": 4,
}
COST_ARITY = {"distance": 2, "door-opening-cost": 1}

# Diagnostics for nonzero outcomes in Fast Downward 26.6's driver/returncodes.py.
EXIT_DETAILS = {
    1: "portfolio found a plan and ran out of memory",
    2: "portfolio found a plan and ran out of time",
    3: "portfolio found a plan and ran out of memory and time",
    10: "translator proved the task unsolvable",
    11: "search proved the task unsolvable",
    12: "search ended without a plan or proof of unsolvability",
    13: "search proved unsolvability within the cost bound",
    20: "translator ran out of memory",
    21: "translator ran out of time",
    22: "search ran out of memory",
    23: "search ran out of time",
    24: "portfolio ran out of memory and time",
}


def read_pddl(path):
    """Read parenthesized forms for structural comparison of our problem pairs."""
    source = re.sub(r";[^\n]*", "", path.read_text(encoding="utf-8").lower())
    stack = [[]]
    for token in re.findall(r"[()]|[^\s()]+", source):
        if token == "(":
            form = []
            stack[-1].append(form)
            stack.append(form)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError(f"{path}: unexpected closing parenthesis")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1 or len(stack[0]) != 1 or not isinstance(stack[0][0], list):
        raise ValueError(f"{path}: expected a single balanced PDDL form")
    return stack[0][0]


def read_problem(path):
    """Return cost assignments and a task signature with their values removed."""
    problem = read_pddl(path)
    if (len(problem) < 2 or problem[0] != "define" or not isinstance(problem[1], list)
            or problem[1][:1] != ["problem"]):
        raise ValueError(f"{path}: expected a PDDL problem")
    sections = problem[2:]
    init_sections = [section for section in sections if section[:1] == [":init"]]
    if len(init_sections) != 1 or [":metric", "minimize", ["total-cost"]] not in sections:
        raise ValueError(f"{path}: expected :init and a total-cost minimization metric")

    costs = {}
    init = init_sections[0]
    for index, fact in enumerate(init[1:], start=1):
        if fact[:1] != ["="]:
            continue
        if len(fact) != 3 or not isinstance(fact[1], list) or not fact[1]:
            raise ValueError(f"{path}: invalid assignment {fact}")
        function = fact[1]
        if function == ["total-cost"]:
            continue
        if (not all(isinstance(token, str) for token in function)
                or function[0] not in COST_ARITY or len(function) != COST_ARITY[function[0]] + 1
                or not isinstance(fact[2], str) or not re.fullmatch(r"[0-9]+", fact[2])):
            raise ValueError(f"{path}: invalid cost assignment {fact}")
        key = tuple(function)
        if key in costs:
            raise ValueError(f"{path}: duplicate cost assignment for ({' '.join(key)})")
        costs[key] = int(fact[2])
        init[index] = ["=", function, "<cost>"]
    return sections, costs


def load_pair(scenario):
    paths = {name: PDDL / "problems" / f"{scenario}-{name}.pddl"
             for name in ("unit", "weighted")}
    unit_task, unit_costs = read_problem(paths["unit"])
    weighted_task, weighted_costs = read_problem(paths["weighted"])
    if unit_task != weighted_task:
        raise ValueError(f"{scenario}: paired tasks differ beyond the name and cost values")
    if any(cost != 1 for cost in unit_costs.values()):
        raise ValueError(f"{scenario}: all unit cost assignments must be 1")
    return paths, weighted_costs


def parse_plan(plan):
    """Read Fast Downward's action lines and its final reported cost."""
    lines = plan.strip().splitlines()
    footer = re.fullmatch(r"; cost = ([0-9]+) \((?:unit|general) cost\)",
                          lines[-1].strip()) if lines else None
    if footer is None:
        raise ValueError("missing Fast Downward plan cost footer")
    actions = []
    for line in lines[:-1]:
        content = line.partition(";")[0].strip().lower()
        if content:
            action = re.fullmatch(r"\(([^()]+)\)", content)
            if action is None or not action[1].split():
                raise ValueError(f"invalid plan action {line!r}")
            actions.append(action[1].split())
    return actions, int(footer[1])


def evaluate_plan(actions, costs):
    total = 0
    for action, *args in actions:
        if action not in ACTION_ARITY:
            raise ValueError(f"unknown action {action!r}")
        if len(args) != ACTION_ARITY[action]:
            raise ValueError(f"unexpected arguments for {action!r}: {args}")
        if action == "move":
            key = ("distance", *args)
        elif action == "open-door":
            key = ("door-opening-cost", args[0])
        else:
            total += 1
            continue
        if key not in costs:
            raise ValueError(f"missing weighted assignment for ({' '.join(key)})")
        total += costs[key]
    return total


def parse_log(log):
    patterns = (
        ("plan_length", r"Plan length: ([0-9]+) step\(s\)\.", int),
        ("planner_cost", r"Plan cost: ([0-9]+)", int),
        ("search_time_s", r"Search time: ([0-9]+(?:\.[0-9]+)?)s", float),
        ("expanded_states", r"Expanded ([0-9]+) state\(s\)\.", int),
    )
    metrics = {}
    for field, pattern, convert in patterns:
        match = re.search(r"^(?:\[t=[^\]\n]+\] )?" + pattern + r"[ \t]*$", log, re.MULTILINE)
        if match:
            metrics[field] = convert(match[1])
    return metrics


def planner_status(returncode):
    if returncode is None or returncode in (21, 23):
        return "timeout"
    if returncode in (10, 11):
        return "unsolvable"
    return "solved" if returncode == 0 else "error"


def run_command(command, directory, timeout):
    """Return the exit code (None on timeout) and wall time; save raw output."""
    with (directory / "planner.log").open("wb") as log:
        start = perf_counter()
        with subprocess.Popen(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              start_new_session=True) as process:
            try:
                stdout, _ = process.communicate(timeout=timeout)
                returncode = process.returncode
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                # Stop the driver and any translator/search subprocess it started.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, _ = process.communicate()
                if isinstance(exc, KeyboardInterrupt):
                    log.write(stdout)
                    raise
                returncode = None
            elapsed = perf_counter() - start
            log.write(stdout)
        return returncode, round(elapsed, 6)


def run_trial(fd, scenario, objective, run, problem, costs, timeout, evidence):
    row = dict(scenario=scenario, objective=objective, run=run, status="error")
    command = [*fd, str(DOMAIN), str(problem), "--search", SEARCH]
    evidence.mkdir()
    with tempfile.TemporaryDirectory(prefix="kpis-fd-") as temporary:
        directory = Path(temporary)
        log_path = directory / "planner.log"
        plan_path = directory / "sas_plan"
        detail = ""
        try:
            returncode, row["total_runtime_s"] = run_command(command, directory, timeout)
            log = log_path.read_text(encoding="utf-8", errors="replace")
            metrics = parse_log(log)
            for field in ("search_time_s", "expanded_states"):
                row[field] = metrics.get(field)
            status = planner_status(returncode)
            if status == "solved":
                if not re.search(r"^search exit code: 0$", log, re.MULTILINE):
                    raise ValueError("missing successful search completion in planner log")
                actions, planner_cost = parse_plan(plan_path.read_text(encoding="utf-8"))
                length = len(actions)
                if (metrics.get("plan_length", length) != length
                        or metrics.get("planner_cost", planner_cost) != planner_cost):
                    raise ValueError("plan file and planner log disagree")
                weighted_cost = evaluate_plan(actions, costs)
                expected = length if objective == "unit" else weighted_cost
                if planner_cost != expected:
                    raise ValueError(f"planner cost {planner_cost} differs from expected {expected}")
                row.update(plan_length=length, planner_cost=planner_cost, weighted_cost=weighted_cost)
            else:
                if returncode is None:
                    detail = f"wall-clock limit of {timeout:g}s"
                else:
                    detail = f"exit code {returncode}"
                    if returncode in EXIT_DETAILS:
                        detail += f": {EXIT_DETAILS[returncode]}"
            row["status"] = status
        except (OSError, ValueError) as exc:
            detail = str(exc)
        finally:
            for artifact in (log_path, plan_path):
                if artifact.is_file():
                    shutil.copyfile(artifact, evidence / artifact.name)
        if detail:
            print(f"{scenario} {objective} run {run}: {row['status']} ({detail})", file=sys.stderr)
    return row


def cost_reduction(unit_weighted_cost, weighted_cost):
    if unit_weighted_cost == 0:
        return None
    return (unit_weighted_cost - weighted_cost) / unit_weighted_cost * 100


def print_summary(trials, scenarios):
    print("Per scenario (medians across complete solved pairs)")
    for scenario in scenarios:
        pairs = [pair for pair in trials if pair[0]["scenario"] == scenario]
        solved = [(unit, weighted) for unit, weighted in pairs
                  if unit["status"] == weighted["status"] == "solved"]
        count = f"{len(solved)}/{len(pairs)} pairs solved"
        if not solved:
            print(f"  {scenario}: {count}")
            continue
        unit_rows, weighted_rows = zip(*solved)
        unit_cost = median(row["weighted_cost"] for row in unit_rows)
        weighted_cost = median(row["weighted_cost"] for row in weighted_rows)
        unit_time = median(row["total_runtime_s"] for row in unit_rows)
        weighted_time = median(row["total_runtime_s"] for row in weighted_rows)
        reductions = [cost_reduction(unit["weighted_cost"], weighted["weighted_cost"])
                      for unit, weighted in solved if unit["weighted_cost"] > 0]
        reduction = f"{median(reductions):.2f}%" if reductions else "n/a"
        print(f"  {scenario}: {count}, weighted cost {unit_cost:g} -> {weighted_cost:g} "
              f"({reduction} reduction), wall time {unit_time:.6f}s / {weighted_time:.6f}s (unit / weighted)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fd", default=str(HERE.parent.parent / "fast-downward.py"),
                        help="path to the Fast Downward 26.6 driver or its executable on PATH")
    parser.add_argument("--scenario", choices=SCENARIOS, action="append",
                        help="scenario to run (repeat to select more than one, default: all)")
    parser.add_argument("--repetitions", type=int, default=1, help="runs per objective (default: 1)")
    parser.add_argument("--timeout", type=float, default=60, help="seconds per run (default: 60)")
    parser.add_argument("--output", type=Path, default=HERE / "results" / "benchmark.csv",
                        help="destination CSV (default: experiments/results/benchmark.csv)")
    args = parser.parse_args()
    if os.name != "posix":
        parser.error("this runner requires POSIX process groups to stop the planner on timeout")
    if args.repetitions < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("repetitions and timeout must be positive and finite")

    driver = Path(args.fd).expanduser()
    if not driver.is_file():
        executable = shutil.which(str(driver))
        if executable is None:
            parser.error(f"Fast Downward driver unavailable at {args.fd!r}; supply its path with --fd")
        driver = Path(executable)
    driver = driver.resolve()
    fd = [sys.executable, str(driver)] if driver.suffix == ".py" else [str(driver)]
    scenarios = tuple(dict.fromkeys(args.scenario or SCENARIOS))
    output = args.output.expanduser().absolute()

    try:
        pairs = {scenario: load_pair(scenario) for scenario in scenarios}
        with tempfile.TemporaryDirectory(prefix="kpis-fd-version-") as temporary:
            directory = Path(temporary)
            returncode, _ = run_command([*fd, "--version"], directory, timeout=10)
            version = (directory / "planner.log").read_text(encoding="utf-8", errors="replace").strip()
            if returncode != 0 or VERSION not in version.splitlines():
                parser.error(f"expected {VERSION} from {driver}, got {version or 'no version output'}")
        output.parent.mkdir(parents=True, exist_ok=True)
        evidence = Path(tempfile.mkdtemp(prefix=f"{output.stem}-logs-", dir=output.parent))
        configuration = (f"{version}\nDriver: {driver}\nSearch: {SEARCH}, {args.repetitions} repetition(s), "
                         f"{args.timeout:g}s timeout per run\nScenarios: {', '.join(scenarios)}\n")
        (evidence / "configuration.txt").write_text(configuration, encoding="utf-8")
        print(f"{configuration}Logs and plans: {evidence}", flush=True)
        trials = []
        for scenario, (paths, costs) in pairs.items():
            for run in range(1, args.repetitions + 1):
                trials.append(tuple(
                    run_trial(fd, scenario, objective, run, path, costs, args.timeout,
                              evidence / f"{scenario}-{objective}-{run}")
                    for objective, path in paths.items()
                ))

        rows = [row for pair in trials for row in pair]
        with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
            pending_csv = Path(temporary) / output.name
            with pending_csv.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            pending_csv.replace(output)
        print_summary(trials, scenarios)
        print(f"CSV: {output}")
        return int(any(row["status"] != "solved" for row in rows))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
