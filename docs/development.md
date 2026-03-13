# AetherNet Development Guide

This guide explains how to set up a local development environment, establish a reliable workflow, and interact with the CI pipeline.

## Recommended Local Setup
Use a Python virtual environment to keep your host system clean. The project dependencies are explicitly tracked in `requirements-dev.txt`.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# 2. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
````

## Developer Workflow & Task Runner

To avoid manual `PYTHONPATH` exports or repetitive shell commands, use the provided `Makefile`.

### Pre-push Checklist

Before committing or pushing changes, run:

```bash
make smoke
```

`make smoke` is the fast validation path for this repo. It runs the default demo path and a fail-fast test pass.

### Common Targets

* `make setup-dev` — install developer dependencies
* `make smoke` — quick local validation before push
* `make test` — run the full test suite
* `make test-fast` — stop on first failing test
* `make compare` — execute all built-in scenarios and generate artifacts
* `make clean-artifacts` — remove generated outputs
* `make reset-env` — clean payload working directories

## CI vs Local Validation

AetherNet includes a minimal GitHub Actions workflow in `.github/workflows/test.yml`.

Recommended habit:

1. run `make smoke` during active development
2. run `make test` before larger changes or merges
3. let CI act as the final remote safety net

## Source vs Generated Files

* **Source-controlled**: `sim/`, `router/`, `bundle_queue/`, `store/`, `metrics/`, `docs/`, `tests/`
* **Generated / ignored**: `artifacts/`, generated payload data under `payloads/` except keep files

