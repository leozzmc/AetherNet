# ADR 0010: Repository Hygiene and Demo Readiness

**Date**: 2026-03-13
**Status**: Accepted

## Context
AetherNet has reached a level of maturity where the core simulation logic is stable, and cross-scenario reporting is functional. However, without standard conventions (`.gitignore`, `Makefile`), the repository risks accumulating generated garbage files (e.g., `artifacts/`, `__pycache__/`) and requires a steep learning curve for new developers to execute tests and demos.

## Decision
We implemented a strict `.gitignore`, a lightweight `Makefile` providing standard targets (`test`, `demo`, `compare`, `clean-artifacts`), and established a `docs/development.md` guide.

## Rationale
1. **Demo & Research Readiness**: Researchers and reviewers should be able to clone the repo, run `make compare`, and immediately look at the JSON outputs without wrestling with `PYTHONPATH` or shell scripts.
2. **Preventing Technical Debt**: Explicitly ignoring `artifacts/` prevents test outputs from bleeding into source control.
3. **No Heavy Tooling**: We chose a `Makefile` over complex Python task runners (like Nox or Invoke) because it is universally understood, POSIX-compliant, and perfectly matches the MVP's lightweight ethos.