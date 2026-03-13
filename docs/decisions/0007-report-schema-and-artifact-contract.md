# ADR 0007: Report Schema and Artifact Contract

**Date**: 2026-03-13
**Status**: Accepted

## Context
As AetherNet added scenario profiles and comparison runners, the output JSON structures and directory layouts began to evolve organically. To prevent downstream tools (or future developers) from breaking due to unannounced renaming of metrics or report keys, we needed to formalize the output contracts.

## Decision
We defined a strict, stable schema for `summarize_report()`, `compare_reports()`, and the Simulator's `build_final_report()`. Additionally, we established the `artifacts/` directory as the standard output destination for all batch runners.

## Rationale
Stabilizing the schema is a prerequisite for moving out of the "prototype" phase. By guaranteeing that keys like `delivered_bundle_ids` and `purged_bundle_ids` will always be present and correctly named, we make AetherNet reliable enough to be used as a backend for future visualizations, latency derivations, or CI/CD regression tests.