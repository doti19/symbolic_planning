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

## Analyze results and create paper figures

The analysis uses Python 3.10 or newer, its standard library, and Matplotlib.
Install the plotting dependency in a virtual environment from the repository root.

```bash
python3 -m venv /tmp/kpis-analysis-venv
source /tmp/kpis-analysis-venv/bin/activate
python3 -m pip install -r experiments/requirements-analysis.txt
```

Analyze the local benchmark CSV with the following command. Fast Downward is
needed only when collecting new benchmark measurements.

```bash
python3 experiments/analyze_results.py \
  --input experiments/results/benchmark.csv \
  --output experiments/figures \
  --expected-repetitions 3
```

The command prints a table and writes the following outputs.

- `experiments/results/summary.csv` contains one row per scenario with median
  actions, planner costs, weighted costs, expanded states, search times, and
  total runtimes for each objective. It also records matched repetition counts,
  the median paired action-count difference, median paired weighted-cost
  reduction, and the number of pairs with a defined reduction.
- `experiments/figures/weighted_cost_comparison.pdf` and `.png` compare the
  plans under the common weighted model.
- `experiments/figures/plan_length_comparison.pdf` and `.png` compare action counts.
- `experiments/figures/expanded_states_comparison.pdf` and `.png` compare planning
  search effort.
- `experiments/RESULTS_ANALYSIS.md` contains the setup, measured results,
  discussion, and limitations as preparation for the seminar paper.

The vector PDFs are sized for a 3.5-inch paper column. PNGs use 300 DPI.
All plots use the same scenario order and colorblind-friendly colors, with
hatching to distinguish objectives in grayscale. Bars display medians, and
integer ticks are used for counts. Medians can be fractional when an even
number of repetitions has different action counts. The default figures and
results directories are Git-ignored. `--summary` and `--report` can redirect the
table and Markdown output. Existing output files are replaced on each run.

Every row must be solved. All benchmark columns must be present, costs and
counts must be nonnegative integers, and repetition numbers must start at 1
and be consecutive with both objectives present. Duplicates, failed runs,
malformed numbers, and incomplete pairs cause an error before figure generation.
A CSV containing a valid subset of scenarios is supported. Without
`--expected-repetitions`, each scenario's repetition count is inferred from its
rows; a final pair absent from both objectives cannot be detected from the CSV
alone. Use `--expected-repetitions 3` when checking the complete seminar dataset.

Blank expanded-state or timing measurements are allowed. If any repetition
lacks one of these measurements, that entire scenario/objective median is
left blank in the summary, shown as `n/a` in figures where relevant, and reported
in terminal warnings and the Markdown report. No partial median is substituted.
Missing measurements in required cost/action columns are rejected.

`cost_reduction_percent` uses each matched pair's `weighted_cost` values,
then takes the median of the defined percentages. A zero unit weighted cost
has an undefined reduction and is counted separately using `cost_reduction_pairs`.
`plan_length_difference` is the median of paired `weighted - unit` action counts.
`optimal_weighted_cost` is the weighted objective's observed median cost under
the benchmark's optimal search configuration. Weighted costs use synthetic cost
units. Summary timing columns are in seconds and retain the distinction between
search time and whole-process runtime.

To regenerate the paper figures from the small saved evidence snapshot, run
the following command. The [evidence guide](evidence/README.md) records its
configuration, provenance, host observations, and limitations.

```bash
python3 experiments/analyze_results.py \
  --input experiments/evidence/benchmark-results.csv \
  --output experiments/figures --expected-repetitions 3
```

The test command above includes analysis fixtures, aggregation and input
validation checks, and PDF/PNG export. It requires Matplotlib but runs without
Fast Downward. To run only the original benchmark tests, use
`python3 -m unittest discover -s experiments -p test_benchmark.py -v`.
