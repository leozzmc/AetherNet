# ADR 0005: Scenario Profiles and Reporting

**Date**: 2026-03-13
**Status**: Accepted

## Context
As AetherNet evolves from a hardcoded demo into an MVP, we need a way to prove that the architecture can handle various space networking anomalies (e.g., long delays, missed windows, expired data). Hardcoding these into `simulator.py` makes testing fragile and demonstration difficult.

## Decision
We introduced a lightweight `Scenario Registry` and an `End-of-Run Report` exporter using standard Python libraries (`argparse`, `json`, `dataclasses`). 

## Rationale
1. **Reproducibility**: Researchers can now run `--scenario delayed_delivery` and consistently get the same behavior and JSON report, which is critical for an experimental platform.
2. **Avoiding Scope Creep**: We deliberately avoided complex CLI frameworks (like Click/Typer) or real Prometheus servers. Generating a JSON report to `stdout` or a file satisfies the immediate need for observability without introducing heavy infrastructural dependencies.