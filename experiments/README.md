# Action-cost benchmark

The benchmark runs each scenario twice, once minimizing the number of actions
and once minimizing weighted action costs. Both runs use `pddl/domain-costs.pddl`
and Fast Downward **26.6** with `--search 'astar(lmcut())'`. The runner checks
that each problem pair has the same task and cost assignments in the same
places, with all variable costs set to 1 in the unit problem.

| Scenario ID | Task |
| --- | --- |
| `cost-nav` | Five-room navigation |
| `eight-room` | Eight-room navigation |
| `door-detour` | Closed-door shortcut versus a detour |
| `object-retrieval` | Retrieve and deliver a book |
| `two-object-retrieval` | Retrieve and deliver a book and a laptop |

## Run the benchmark

Use Python 3 and a built Fast Downward 26.6 installation on macOS or Linux.
From the repository root, run all five pairs with the sibling installation
described in the [project README](../README.md).

```bash
python3 ../fast-downward.py --version
python3 experiments/benchmark.py
```

With Fast Downward installed elsewhere, provide the path to its driver. This
example runs only the two-object scenario, with three repetitions per objective.

```bash
python3 experiments/benchmark.py \
  --fd /path/to/fast-downward-26.6/fast-downward.py \
  --scenario two-object-retrieval \
  --repetitions 3 --timeout 60 \
  --output experiments/results/two-object-retrieval.csv
```

You can repeat `--scenario` to select several pairs. The defaults are one
repetition per objective, 60 seconds per run, and
`experiments/results/benchmark.csv`. Each run uses its own temporary working
directory. The runner saves the original combined planner output and any plan
file in a fresh `*-logs-*` directory beside the CSV, along with the planner
version and run settings in `configuration.txt`. The default results directory
is Git-ignored. Use distinct CSV paths to retain separate measurements.

## Read the results

The CSV contains one row per planner invocation. An empty cell means the
measurement was unavailable or the run did not produce a usable plan.

| Column | Meaning |
| --- | --- |
| `scenario` | Scenario ID from the table above |
| `objective` | `unit` minimizes action count and `weighted` minimizes total action cost |
| `run` | Repetition number, starting at 1 |
| `status` | `solved`, `unsolvable` (proven by Fast Downward), `timeout`, or `error` |
| `plan_length` | Number of actions in the saved plan |
| `planner_cost` | Plan cost reported by Fast Downward under that run's objective |
| `weighted_cost` | Cost of the saved plan using the scenario's weighted problem |
| `search_time_s` | Seconds on Fast Downward's `Search time:` line |
| `total_runtime_s` | Wall-clock seconds for the whole planner process, including translation and search |
| `expanded_states` | Number of states Fast Downward reports expanding |

`timeout` covers the runner's wall-clock limit and timeouts reported by the
translator or search. Incomplete searches, proofs limited to a cost bound,
memory exhaustion, and portfolio resource outcomes are recorded as `error`.

Use `weighted_cost` to compare the two plans. The evaluator looks up each
`move` using the directed `(distance from to)` assignment and each `open-door`
using `(door-opening-cost door)`. `pick-up`, `put-on-table`, `hand-over`,
`open-cabinet`, and `take-from-cabinet` each cost 1 in the domain. Unknown
actions, missing cost assignments, or inconsistent planner costs make the
run an error. If several plans have the same minimum action count, the measured
baseline is the plan Fast Downward selects among those ties.

The terminal summary uses complete solved pairs. For each pair it computes
`100 * (unit plan's weighted cost - weighted plan's weighted cost) / unit plan's weighted cost`.
The percentage is undefined when the unit plan's weighted cost is zero. With
repetitions, the summary reports median costs, median wall times, and the
median of defined per-pair reductions. The command exits with status 1 if any
run fails to produce a usable solution. Consult its log directory for details.

To reproduce the comparison, use the same PDDL revision, planner build,
scenario selection, repetition count, and timeout. Record the machine and
operating system when comparing runtimes. The runner executes trials serially,
with the unit trial first in each pair. The tests below run without Fast Downward
and include the captured two-object plans evaluated against the checked-in
weighted problem.

```bash
python3 -m unittest discover -s experiments -v
```
