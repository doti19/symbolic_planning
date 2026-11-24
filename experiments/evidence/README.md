# Saved benchmark evidence

`benchmark-results.csv` preserves the measurements from the complete local
`experiments/results/benchmark.csv` from the benchmark run preceding the
results-analysis implementation, with CSV line endings normalized to LF for
Git. Values and row ordering are unchanged. It contains 30 solved runs. Every recorded
plan length, planner cost, weighted cost, search time, and expanded-state count
was checked against the corresponding local plan and original planner log
before copying. Total runtime is the benchmark's recorded wall-clock measurement.

The snapshot's SHA-256 is
`51b7986a9870e8451425823f5ceb796e4aed95069a7a5860521f9243276c0f88`.
The original source CSV's SHA-256, including its CRLF line endings, is
`a5b2ba03e028f94a2a730f05b4b7299252c87d14eba394ae96a7d9ff7fb24843`.
The CSV and this guide are eligible for version control. Generated figures,
summaries, caches, and original planner logs remain in ignored directories.

## Experiment configuration

| Setting | Recorded value |
| --- | --- |
| Repository revision | `6e7670ab67aa42e8e2bfa93f3ea1991a1db344a8` |
| Planner | Fast Downward 26.6, local release build |
| Planner source revision | Driver reports `git revision [release]: unknown` |
| Search for both objectives | `astar(lmcut())` |
| Domain | `pddl/domain-costs.pddl` |
| Scenarios | `cost-nav`, `eight-room`, `door-detour`, `object-retrieval`, `two-object-retrieval` |
| Repetitions | Three per objective in each scenario |
| Limit | 60 wall-clock seconds per invocation |
| Order | Serial execution, unit run followed by weighted run for each repetition |
| Independent plan validation | VAL was unavailable in the reported benchmark |

The repository revision and execution were recorded in the working session.
The retained local `benchmark-logs-1f14k344/configuration.txt` confirms the
planner version, search, scenarios, repetitions, and timeout. Logs do not
record the planner's exact source revision or a wall-clock start timestamp.

The host inspected when archiving this snapshot on 20 November 2026 was a
MacBook Pro (Mac16,8), Apple M4 Pro, 24 GB memory, running macOS 26.6.2
(build 25G83), arm64. These details came from `system_profiler`, `sw_vers`, and
`uname`; the original benchmark CSV and driver log do not record host details.
Analysis and figure export were checked with Python 3.13.5 and Matplotlib 3.10.7.

## Reproduce the analysis

From the repository root, install the dependency in a virtual environment,
then analyze the saved measurements without running Fast Downward.

```bash
python3 -m venv /tmp/kpis-analysis-venv
source /tmp/kpis-analysis-venv/bin/activate
python3 -m pip install -r experiments/requirements-analysis.txt
python3 experiments/analyze_results.py \
  --input experiments/evidence/benchmark-results.csv \
  --output experiments/figures \
  --expected-repetitions 3
```

This regenerates the three PDF/PNG figures, `experiments/results/summary.csv`,
and `experiments/RESULTS_ANALYSIS.md`. Summaries and figures use observed
medians. Reductions are calculated within matched repetition numbers, then
aggregated by their median. All cost, action-count, and expanded-state
measurements are identical across the three repetitions of each objective
in this snapshot. Timing measurements vary.

To collect new measurements, use the recorded repository revision's PDDL and
benchmark runner with a built Fast Downward 26.6 installation. Write to a
separate file to retain the saved evidence.

```bash
python3 experiments/benchmark.py --fd ../fast-downward.py \
  --repetitions 3 --timeout 60 --output experiments/results/rerun.csv
python3 experiments/analyze_results.py --input experiments/results/rerun.csv \
  --output experiments/figures --expected-repetitions 3
python3 -m unittest discover -s experiments -v
node --test presentation/vfg.test.mjs
```

## Interpretation and limits

Compare the `weighted_cost` measurements for both objectives. Unit-cost
planner costs count actions. Movement uses the weighted problem's directed
`distance` assignments, opening a door uses `door-opening-cost`, and the five
manipulation action types each cost 1. The recorded unit and weighted tasks
share their logical definitions.

Inspection of the retained plans confirmed different routes through the lab
and hallway in five-room navigation, and through the lab and library in
eight-room navigation. The door-detour weighted plan avoids opening the
service door. Both object-retrieval plans use that door on a round trip and
achieve the same weighted cost. The two-object weighted plan collects the
laptop before the book and returns via the library, avoiding the door.

The environments are small and manually designed, with synthetic costs.
Three repetitions on five deterministic tasks characterize repeatability on
these tasks. They support no significance tests or claim of physical energy
savings. Very short search times and process overhead limit runtime
comparisons. Independent VAL validation and broader real-world evaluation
remain outside this evidence. See the [results analysis](../RESULTS_ANALYSIS.md)
for the measured cost/action trade-offs.
