# AetherNet Demo Note (Phase-5 → Demo Layer)

## Purpose

This document describes:

- what was implemented specifically for the demo layer
- how routing policy comparison is exposed
- how to run and interpret demo results
- what guarantees are provided (determinism, reproducibility)

This document is intended for:

- AI agent handoff
- engineers onboarding to demo layer
- reviewers evaluating routing behavior

---

## What Demo Layer Adds

The demo layer introduces:

### 1. Routing Mode Control Surface

Routing policy is now a first-class experimental dimension:

- baseline
- contact_aware
- multipath

Accessible via:

```bash
python3 demo.py --routing-mode <mode>
```

---

### 2. Scenario → Policy Comparison

Demo scenarios are now designed to:

- expose routing differences
- produce divergence in outcome
- validate routing correctness

---

### 3. Deterministic Output Contract

Each demo run produces:

- JSON summary
- CSV summary

All outputs are:

- deterministic
- reproducible
- comparable across runs

---

## Demo Scenarios

### default_multihop

Purpose:

- validate base DTN forwarding
- confirm simulator correctness

Expected:

- all routing modes succeed

---

### multipath_competition

Purpose:

- demonstrate multi-path advantage

Behavior:

- baseline may choose wrong relay
- multipath evaluates candidates

Expected:

- baseline → fail
- multipath → success

---

### contact_timing_tradeoff

Purpose:

- demonstrate timing-aware routing

Behavior:

- only one path is temporally valid
- requires future contact reasoning

Expected:

- baseline → fail
- contact_aware → success

---

## Demo Execution Model

```text
Scenario → Simulator → Routing Policy → Forwarding → Metrics → Artifact
```

Routing decision is the only variable.

Everything else is held constant.

---

## Guarantees

### Determinism

- same scenario → same result
- same routing mode → same result

### Isolation

- routing policies do not mutate scenario
- comparison is fair

### Reproducibility

- all outputs are artifact-backed
- can be replayed via same inputs

---

## Known Limitations

- no probabilistic behavior yet
- no adversarial modeling yet
- routing still heuristic-based

---

## Why This Matters

The demo layer establishes:

> routing policy as a controllable experimental dimension

This is the foundation for:

- Phase-6 probabilistic routing
- adversarial evaluation
- security-aware routing

---
