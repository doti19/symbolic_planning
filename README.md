# Symbolic Planning for a Mobile Companion Robot

**Seminar:** KPIS Seminar 2026/27  
**Team:** 1  
**Students:** Saminas Gigar and Alexandra Hooser  

This project models a mobile companion robot and part of the computer science
building using the [Planning Domain Definition Language
(PDDL)](https://planning.wiki/ref/pddl). The robot can navigate between rooms,
pick up objects with its left or right gripper, and put objects on tables.
The domain will be extended with additional robot, environment, and
interaction capabilities as the project progresses.

The Team 1 extension focuses on **action costs**. In particular, we will model
costs such as travel distance and manipulation actions, then investigate how
minimizing total cost changes the resulting plans compared with minimizing the
number of actions.

## Repository layout

```text
symbolic-planning/
├── pddl/
│   ├── domain.pddl
│   ├── animations/
│   │   └── symbolic_planning_AP.pddl
│   └── problems/
│       ├── navigation.pddl
│       ├── object-delivery.pddl
│       ├── two-object-transport.pddl
│       ├── gripper-capacity-test.pddl
│       ├── human-handover.pddl
│       ├── door-navigation.pddl
│       └── cabinet-retrieval.pddl
└── README.md
```

The project is currently stored inside a Fast Downward checkout. The
`fast-downward.py` driver and `build.py` script are therefore one directory
above this folder.

## Planimation

The [standalone animation profile](pddl/animations/symbolic_planning_AP.pddl)
turns a building plan into a 2D floor plan. See the
[Planimation guide](pddl/animations/README.md) for upload steps, the editable
sprite source, and validation frames for the seminar demos.

For the seminar, the [local VFG player](presentation/README.md) displays
Planimation-generated plans on a larger canvas and exports video clips.

## Prerequisites

- Python 3
- A C++ compiler
- CMake
- GNU Make

On macOS, install the Xcode Command Line Tools if they are not already
available:

```bash
xcode-select --install
```

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install cmake g++ make python3
```

## Installing Fast Downward

From the Fast Downward project root:

```bash
cd /path/to/fast-downward-26.6
python3 build.py
```

This creates the default release build in `builds/release/`. Test the build
with a bundled benchmark:

```bash
python3 fast-downward.py \
  misc/tests/benchmarks/miconic/s1-0.pddl \
  --search "astar(lmcut())"
```

More detailed build and platform information is available in
[`../BUILD.md`](../BUILD.md).

## Running the project examples

Run these commands from the Fast Downward project root:

### Navigation

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/navigation.pddl \
  --search "astar(lmcut())"
```

### Object delivery

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/object-delivery.pddl \
  --search "astar(lmcut())"
```

### Two-object transport

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/two-object-transport.pddl \
  --search "astar(lmcut())"
```

### Human handover

This problem models the robot picking up a book, navigating to a professor,
and handing over the book.

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/human-handover.pddl \
  --search "astar(lmcut())"
```

### Door navigation

This problem models the robot opening a closed door before moving from the
office to the meeting room.

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/door-navigation.pddl \
  --search "astar(lmcut())"
```

### Cabinet retrieval

This problem models the robot navigating to the office, opening a cabinet,
retrieving a book, and delivering it to the meeting-room table.

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/cabinet-retrieval.pddl \
  --search "astar(lmcut())"
```

Fast Downward prints the generated plan and search statistics in the
terminal. The default plan file is `sas_plan`.

The same commands can be run from this directory by replacing
`python3 fast-downward.py` with `python3 ../fast-downward.py` and removing the
`symbolic-planning/` prefix from the PDDL paths.

## Comparing action costs and plan length

The baseline planner minimizes the total cost of the actions as represented by
the task. For the Team 1 experiments, we will add PDDL action costs (for
example, different movement costs for different distances) and compare them
with unit-cost planning.

A unit-cost comparison can be run with:

```bash
python3 fast-downward.py \
  symbolic-planning/pddl/domain.pddl \
  symbolic-planning/pddl/problems/object-delivery.pddl \
  --search "astar(lmcut(), cost_type=one)"
```

For each experiment, record at least:

- whether a plan was found;
- plan length (number of actions);
- total plan cost;
- runtime;
- search effort, such as expanded and generated states;
- whether the planner terminated successfully.

The cost-aware and unit-cost versions should be tested on the same problem
instances so that their plans and performance can be compared fairly.

## Optional PDDL tools

The [PDDL extension by Jan
Dolejsi](https://marketplace.visualstudio.com/items?itemName=jan-dolejsi.pddl)
provides syntax highlighting and editor diagnostics. Its optional VAL
validator can independently check generated plans. VAL is not required to run
Fast Downward, which has its own PDDL parser.

On Apple Silicon, the extension's automatic VAL download may not provide a
`darwin arm64` binary. In that case, keep using native Apple Silicon VS Code
and Fast Downward, or install/build VAL separately if independent plan
validation is needed.

## Related tools

- [Pyperplan](https://github.com/aibasel/pyperplan) — lightweight Python
  planner.
- [Unified Planning](https://unified-planning.readthedocs.io/en/stable/) —
  Python framework for modeling planning problems and using different
  planning engines.
- [Fast Downward](https://www.fast-downward.org/) — configurable classical
  planning system used for the main experiments.
- [VAL](https://github.com/KCL-Planning/VAL) — optional independent plan
  validator.
