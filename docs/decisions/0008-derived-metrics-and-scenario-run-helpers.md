# ADR 0008: Derived Metrics and Scenario Run Helpers

**Date**: 2026-03-13
**Status**: Accepted

## Context
As the number of scenarios grew, the boilerplate code to set up, run, and evaluate a scenario became scattered across bash scripts (`run_compare.sh`) and the simulator's `main()` function. Furthermore, raw metric counters (e.g., `bundles_delivered_total: 3`) lack immediate context without knowing how many bundles were initially injected.

## Decision
1. We introduced `sim/run_helpers.py` to encapsulate the setup/teardown of temporary files and the execution of the simulator.
2. We added "Derived Metrics" (e.g., ratios and categorical outcomes) directly into the reporting summarizer.

## Rationale
Extracting the `run_helpers` completely eliminated the technical debt in our Bash scripts, providing a clean Python API that can be utilized by CI pipelines and Pytest suites. Deriving ratios and outcome categories at the reporting layer avoids cluttering the core DTN Engine with analytical logic, adhering to our principle of keeping the MVP architecture clean and modular.