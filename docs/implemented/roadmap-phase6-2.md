
# AetherNet Roadmap

## Phase-6 / Phase-7: Decision Intelligence → Runtime Showcase

---

## Overview

AetherNet has evolved from a deterministic DTN simulator into a:

> **deterministic, security-aware routing decision system with adaptive runtime showcase capabilities**

This roadmap reflects:

- Phase-6: decision + evaluation + demo layer (complete)
- Phase-7: runtime bridge + adaptive + showcase (complete as CLI showcase layer)
- Next: full runtime integration + visualization

---

# Phase-6: Deterministic Security-Aware Decision Layer

## Completed Waves

### Core foundation

- [x] Wave-73: Controlled Randomness Foundation
- [x] Wave-74: Reliability Trace System
- [x] Wave-75: Adversarial Trace Framework
- [x] Wave-76: Scenario Generator

---

### Context and scoring

- [x] Wave-77: Routing Context Abstraction
- [x] Wave-78: Probabilistic Routing Scoring

---

### Evaluation and security

- [x] Wave-79: Policy Evaluation Engine
- [x] Wave-80: Security Signal Layer
- [x] Wave-81: Security-Aware Routing Decision
- [x] Wave-82: Benchmark Pack

---

### Demo layer and artifact system

- [x] Wave-83: Documentation / Integration Closure
- [x] Wave-84: Phase-6 Demo Scenario Registry
- [x] Wave-85: Artifact Export Layer
- [x] Wave-86: Human-Readable Demo Report Builder
- [x] Wave-87: Minimal Demo Bridge and Comparison Mode

---

## Phase-6 Status

Phase-6 is **complete** as a deterministic decision and evaluation subsystem.

### Capabilities

- deterministic scenario generation
- routing context extraction
- probabilistic scoring
- security signal generation
- security-aware decision artifacts
- benchmark packaging
- artifact export
- human-readable reporting
- scenario comparison

---

## Phase-6 Boundaries

Phase-6 intentionally does NOT include:

- runtime forwarding-loop integration
- adaptive routing behavior
- visualization/dashboard layer
- multi-hop path synthesis

These are deferred to Phase-7 and beyond.

---

# Phase-7: Runtime Bridge, Adaptive Policy, and Showcase

Phase-7 introduces a runtime-facing layer built on top of Phase-6 outputs.

---

## Completed Waves

### Runtime bridge

- [x] Wave-89: Phase-6 Runtime Bridge (avoid filtering)
- [x] Wave-90: Preferred/Allowed Prioritization

---

### Observability and metrics

- [x] Wave-91: Routing Impact Metrics

---

### Adaptive runtime layer

- [x] Wave-92: Deterministic Adaptive Runtime Policy
  - conservative
  - balanced
  - aggressive

---

### Policy automation

- [x] Wave-93: Policy Comparison Runner

---

### Presentation and publishing

- [x] Wave-94: Showcase Report Builder
- [x] Wave-95: CLI Showcase Script
- [x] Wave-96: Documentation / Release Sync

---

## Phase-7 Status

Phase-7 is **complete as a runtime showcase layer**.

### Capabilities

- runtime filtering of unsafe links
- priority-aware routing candidates
- deterministic adaptive routing modes
- routing impact measurement
- automated policy comparison
- publishable CLI showcase

```bash
python scripts/run_phase6_showcase.py
````

---

## Phase-7 Boundaries

Phase-7 currently:

* does NOT globally modify the Phase-5 simulator loop
* does NOT enable adaptive routing inside live simulation by default
* does NOT include visualization/dashboard

This layer is:

> a deterministic runtime control and demonstration layer, not yet a full live routing system

---

# Current System State

```text
Simulation Core (Phase-1~5)        ✔ complete
Decision Layer (Phase-6)           ✔ complete
Runtime Showcase (Phase-7)         ✔ complete
Live Integration                  ⏳ pending
Visualization                     ⏳ pending
```

---

# Next Milestones

## Phase-7.5: Live Runtime Integration

Goal:

> connect Phase-6 decision + Phase-7 adaptive policy into the actual simulator loop

Planned:

* enable adapter inside routing policies
* allow mode selection per run
* measure impact inside full simulation
* maintain deterministic guarantees

---

## Phase-8: Visualization Layer

Goal:

> make routing behavior observable

Planned:

* CLI comparison enhancements
* structured export for UI
* timeline / event visualization
* Streamlit / dashboard layer (optional)

---

## Phase-9: Advanced Routing Intelligence

Goal:

> move from link-level decisions to path-level reasoning

Planned:

* multi-hop secure path synthesis
* route-level risk modeling
* policy tournament systems
* extended benchmark suites

---

## Phase-10: Research Extensions (Optional)

* probabilistic uncertainty modeling
* constrained optimization routing
* reinforcement learning (optional, non-default)
* hybrid deterministic + learned policies

---

# Summary

AetherNet has completed:

```text
Phase-6: deterministic decision system
Phase-7: runtime bridge + adaptive showcase
```

The system now provides:

* reproducible routing evaluation
* security-aware decision modeling
* deterministic adaptive runtime behavior
* policy comparison automation
* publishable CLI showcase

Next evolution:

> from **demonstration system → live adaptive routing system**
