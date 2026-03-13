# ADR 0011: Developer Dependencies and CI Readiness

**Date**: 2026-03-13
**Status**: Accepted

## Context
AetherNet's core architecture and test suite are stable. However, as the repository matures and potentially invites other researchers or contributors, relying on implicit local setups (e.g., assuming `pytest` is manually installed) leads to the "it works on my machine" anti-pattern. We needed to formally declare developer dependencies and establish a baseline Continuous Integration (CI) pipeline.

## Decision
1. We introduced `requirements-dev.txt` to explicitly track testing dependencies (currently just `pytest`).
2. We added a lightweight GitHub Actions workflow (`.github/workflows/test.yml`) to automatically trigger the test suite on pushes and PRs.
3. We introduced a `make smoke` target as a standardized local pre-push validation step.

## Rationale
We chose `requirements-dev.txt` over heavier package managers like `Poetry` or `Pipenv` because AetherNet is an MVP research prototype, not a published PyPI library. The goal is low maintenance overhead. The CI workflow is intentionally simple—acting as a safety net to ensure contract tests (schemas, artifacts, workflows) remain green without introducing complex matrix builds or deployment jobs.