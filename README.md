# AetherNet

**A Secure Delay-Tolerant Distributed Infrastructure Prototype for Space Networks**

## Project Purpose
AetherNet explores how to build a secure, contact-aware, delay-tolerant message infrastructure for space-like environments characterized by intermittent connectivity and extreme latency.

## AetherNet vs LunarNet
- **AetherNet**: the core platform, routing policies, and simulation architecture
- **LunarNet**: the reference deployment scenario using an `Earth ↔ LEO ↔ Moon` topology

## Current MVP Capabilities
This repository provides a repeatable, application-layer DTN experimental platform featuring:
- contact-aware forwarding driven by contact windows
- store-carry-forward behavior using a filesystem-backed DTN store
- strict-priority delivery where telemetry is forwarded ahead of science data
- multi-hop simulation across `lunar-node -> leo-relay -> ground-station`
- retention and expiry handling for stale bundles
- built-in experimental scenarios such as delayed delivery and expiry before contact
- machine-readable JSON reports, scenario comparisons, and lightweight lifecycle timing summaries

## Quickstart

### 1. Environment setup
AetherNet requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
````

### 2. Local validation

Run a quick local validation before pushing:

```bash
make smoke
```

### 3. Run one scenario

Using the Makefile shortcut:

```bash
make demo
```

Directly via script:

```bash
./scripts/run_demo.sh
```

### 4. Run all built-in scenarios

Using the Makefile shortcut:

```bash
make compare
```

Directly via script:

```bash
./scripts/run_compare.sh
```

Generated outputs are written under `artifacts/`. See `docs/artifacts.md` for details.

### 5. Run tests

```bash
make test
```

or:

```bash
pytest tests/
```

## Developer Ergonomics & CI

The repo includes:

* `requirements-dev.txt` for developer dependencies
* a lightweight `Makefile` for common tasks
* a minimal GitHub Actions workflow for automated test validation

Useful commands:

* `make setup-dev`
* `make smoke`
* `make demo`
* `make compare`
* `make test`

## Current Limitations / Non-Goals

The following remain intentionally out of scope for the current MVP:

* real network transport (HTTP, gRPC, TCP/UDP data plane)
* distributed task scheduling or Kubernetes/K3s orchestration
* orbital mechanics or RF-layer physical simulation
* database-backed persistence
* production observability stack

For more details, see:

* `docs/development.md`
* `docs/reports.md`
* `docs/artifacts.md`


----