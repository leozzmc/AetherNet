# ADR 0006: Scenario Comparison and Report Summaries

**Date**: 2026-03-13
**Status**: Accepted

## Context
As AetherNet stabilizes as an MVP, we need a way to prove that our DTN architecture behaves correctly across various edge cases (e.g., normal flow vs. delayed delivery vs. data expiration). Running these manually and inspecting terminal logs is error-prone and doesn't scale for research presentations.

## Decision
We implemented a lightweight reporting extraction module (`sim/reporting.py`) and a batch runner script (`scripts/run_compare.sh`). The runner executes all registered scenarios and aggregates their outcomes into a single `comparison.json` file.

## Rationale
1. **Reproducible Experiments**: A single command now generates the full suite of evidence proving the system's correctness.
2. **Avoiding Heavy CLI/Frameworks**: Embedding the batch logic inside a Bash-invoked Python snippet keeps `simulator.py` perfectly clean and strictly focused on single-run simulation.
3. **Data-Driven Evaluation**: By reducing deep JSON metrics into flat summary fields (e.g., `delivered_bundle_count`), we pave the way for future data visualization and dashboarding without complicating the core codebase.