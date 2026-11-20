# Experimental results analysis

## Experimental setup

The input `benchmark-results.csv` contains 30 solved runs across 5 scenarios, with 3 repetitions per objective. The robot benchmark uses Fast Downward 26.6 with `astar(lmcut())` for both objectives. The input CSV stores measurements. Planner configuration and provenance for the saved snapshot are documented in [the evidence guide](evidence/README.md).

Unit-cost planning minimizes action count. Both resulting plans are evaluated with the weighted problem's directed movement distances, door-opening costs, and unit manipulation costs. Each objective's metrics are medians over all its repetitions. Cost reduction and action-count difference are computed within matched repetition numbers and then summarized by their medians. Zero-cost baselines have undefined percentage reductions.

## Results

| Scenario | Pairs | Unit actions | Weighted actions | Unit plan weighted cost | Weighted plan weighted cost | Reduction (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cost-nav | 3 | 2 | 3 | 15 | 9 | 40.00 |
| eight-room | 3 | 3 | 4 | 18 | 9 | 50.00 |
| door-detour | 3 | 2 | 4 | 14 | 9 | 35.71 |
| object-retrieval | 3 | 5 | 5 | 18 | 18 | 0.00 |
| two-object-retrieval | 3 | 10 | 12 | 30 | 25 | 16.67 |

The figures show median weighted cost, action count, and expanded states. Expanded states measure planning search effort. Weighted action cost measures the modeled execution objective.

## Discussion

- **cost-nav**. The five-room model offers a two-step route through the lab and a longer route through the hallway and office. Their movement costs can favor the longer route. The observed median paired action-count difference is +1, with weighted costs of 15 and 9 for unit and weighted planning.
- **eight-room**. The eight-room model also offers a route through the library and classroom, whose low movement costs can offset additional actions. The observed median paired action-count difference is +1, with weighted costs of 18 and 9 for unit and weighted planning.
- **door-detour**. The service-door shortcut requires a costly opening action. The weighted objective balances that cost against traveling around the door. The observed median paired action-count difference is +2, with weighted costs of 14 and 9 for unit and weighted planning.
- **object-retrieval**. Object retrieval includes both the outward and return journey and a handover. A door-opening cost is paid once, which can make the shortcut worth using for a round trip under both objectives. The observed median paired action-count difference is +0, with weighted costs of 18 and 18 for unit and weighted planning.
- **two-object-retrieval**. Retrieving two objects combines route selection with pickup and delivery order. Additional movement actions can replace an expensive door opening and reduce accumulated weighted cost. The observed median paired action-count difference is +2, with weighted costs of 30 and 25 for unit and weighted planning.

## Limitations

These are small, manually designed building environments with synthetic action costs. The 3 repetitions per objective across these deterministic tasks restrict generalization to larger or real-world robotic environments. Repetitions measure repeatability on each task and do not provide independent problem instances. No significance tests are performed.

Planning times are extremely short in the saved benchmark. Search time comes from the planner's `Search time:` measurement, while total runtime includes translation and process overhead. Tiny differences cannot establish a runtime advantage. The previously reported benchmark had no independent VAL plan validation. Modeled cost reductions do not establish physical energy savings.
