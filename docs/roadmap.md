# AetherNet Roadmap

**AetherNet**
A Secure Delay-Tolerant Distributed Infrastructure Prototype for Space Networks

This roadmap describes the planned evolution of AetherNet from a **Phase-1 DTN transport simulator** into a **research-grade space networking platform**.

The purpose of this document is to help:

* new engineers onboard quickly
* future ChatGPT sessions continue development safely
* contributors understand architectural priorities
* research users understand the simulator's long-term direction

---

# 1. Current Status

AetherNet has completed:

```text
Phase-1   core DTN simulator
Phase-2   transport reliability baseline
Phase-2.2 observability and research tooling
```

Current system capabilities include:

* deterministic scenario execution
* contact-window-driven forwarding
* store-carry-forward persistence
* strict priority queueing
* deterministic fragmentation and reassembly
* partial transmission helper
* fragment retransmission helper
* fragment garbage collection
* custody transfer baseline
* contact plan parser
* experiment runner
* reporting and comparison
* research visualization spec generation
* artifact export

AetherNet is now ready to transition from **transport realism** into **routing research**.

---

# 2. Guiding Principles

All future development should preserve the following properties:

## Determinism

AetherNet is first and foremost a **deterministic simulator**.
The same inputs should produce the same outputs.

## Incremental Development

Each Wave should:

* be small
* have clear boundaries
* include tests
* avoid unnecessary refactors

## Additive Architecture

New features should prefer:

* new helper modules
* policy layers
* clear interfaces
* low coupling

## Research Utility

Every major addition should improve one or more of:

* realism
* experimentability
* observability
* reproducibility

---

# 3. Completed Roadmap

## Phase-1: Core DTN Simulator

Completed baseline:

* scenario system
* simulator clock and tick execution
* contact window scheduling
* store-carry-forward
* strict priority queue
* multi-hop forwarding
* baseline reporting

---

## Phase-2: Transport Reliability

Completed Waves:

### Wave-26 — Contact-Aware Fragmentation

Added contact-capacity-aware fragmentation planning.

### Wave-27 — Partial Contact Transmission

Added helper logic for splitting a bundle into:

* transmitted part
* residual part

### Wave-28 — Contact Plan Parser

Added structured contact-plan parsing from JSON-compatible input.

### Wave-29 — Custody Transfer Baseline

Added custody metadata and deterministic custody helpers.

### Wave-30 — Fragment Retransmission

Added retransmission eligibility and retransmission-ready fragment cloning.

### Wave-31 — Fragment Garbage Collection

Added deterministic fragment-set garbage collection in the reassembly buffer.

### Wave-32 — Fragment Metrics Separation

Separated fragment metrics from bundle metrics.

### Wave-33 — Fragment Artifact Cleanup

Improved report/output clarity for fragment-specific summaries.

### Wave-34 — Experiment Runner

Added deterministic batch execution for scenario experiments.

### Wave-35 — Research Visualization Spec

Added visualization-spec builder for comparison outputs.

### Wave-36 — Artifact Export

Added deterministic JSON artifact export for:

* batch results
* aggregate comparisons
* visualization specs
* manifests

---

# 4. Phase-3: Routing Layer

Phase-3 focuses on the **routing brain** of AetherNet.

The simulator already knows how to:

* store bundles
* fragment bundles
* retry fragments
* collect metrics
* export results

What it still lacks is a mature, pluggable routing decision framework.

This phase introduces **routing policies**, **route scoring**, and **contact-aware path selection**.

---

## Wave-37 — Routing Policy Framework

Goal:

Create a routing policy abstraction so that multiple routing algorithms can be plugged into AetherNet.

Planned capabilities:

* define a routing policy interface
* allow simulator/forwarding engine to delegate next-hop decisions
* keep default routing simple and deterministic
* preserve backward compatibility

Likely components:

```text
router/routing_policy.py
router/policies/
```

Expected outputs:

* policy interface
* baseline direct-contact policy
* tests for policy selection behavior

---

## Wave-38 — Static Routing Baseline

Goal:

Add a simple static routing policy to establish a stable, debuggable routing baseline.

Planned capabilities:

* explicit route mapping
* predictable hop sequences
* route validation for known topologies

Example:

```text
lunar-node -> leo-relay -> ground-station
```

Why this matters:

Before implementing complex routing, the simulator needs a strong baseline policy for comparison.

---

## Wave-39 — Contact-Aware Routing

Goal:

Make routing decisions aware of **future contact windows**.

Planned capabilities:

* inspect contact plan before selecting next hop
* hold bundles if a better future contact is about to open
* avoid naive immediate forwarding when it harms delivery

Research value:

This is the first step toward **time-aware DTN routing**.

---

## Wave-40 — Route Scoring Engine

Goal:

Introduce route scoring to compare candidate paths.

Possible scoring dimensions:

* earliest arrival
* hop count
* delivery probability
* expiry risk
* storage pressure

Expected outputs:

* pluggable scoring function
* deterministic path ranking
* route decision debug output

---

## Wave-41 — CGR-lite

Goal:

Implement a simplified **Contact Graph Routing** baseline.

Scope:

* not full NASA-grade CGR yet
* enough to model time-expanded routing logic
* compute future-aware delivery paths across scheduled contacts

Core ideas:

* time-varying graph
* contact window graph edges
* earliest-arrival route selection

This will likely be the first major research milestone after transport completion.

---

## Wave-42 — Routing Metrics

Goal:

Add routing observability.

Planned metrics:

* route choice count
* average hop count
* route changes
* first-hop decision timing
* failed routing decisions
* per-policy delivery ratio

This wave allows **routing algorithms to be compared experimentally**.

---

# 5. Phase-4: Advanced DTN Research

Phase-4 expands AetherNet from a routing simulator into a broader **DTN reliability and network stress research platform**.

---

## Wave-43 — Congestion Control

Goal:

Model congestion-aware transport and storage pressure behavior.

Possible features:

* queue overflow policy
* congestion-triggered drops
* congestion-aware forwarding decisions
* delivery degradation under bottlenecks

---

## Wave-44 — Priority / QoS

Goal:

Refine priority handling beyond strict queue ordering.

Possible features:

* differentiated service classes
* priority aging
* policy-dependent forwarding
* science vs telemetry tradeoffs

---

## Wave-45 — Storage Pressure Modeling

Goal:

Simulate realistic node storage constraints.

Possible features:

* finite store capacity
* eviction policies
* storage occupancy metrics
* relay pressure scenarios

---

## Wave-46 — Opportunistic Routing

Goal:

Support more DTN-native forwarding strategies.

Possible strategies:

* epidemic-inspired forwarding
* spray-and-wait variants
* opportunistic custody handoff
* hold-vs-forward experiments

---

## Wave-47 — Failure / Partition Modeling

Goal:

Introduce explicit network failure scenarios.

Possible cases:

* lost contacts
* relay failure
* node outage
* long partitions
* intermittent rejoining

This is especially valuable for space-network resilience research.

---

## Wave-48 — Multi-Path Forwarding

Goal:

Allow bundles or fragments to exploit multiple potential paths.

Possible features:

* redundant forwarding
* path diversity experiments
* resilience under link loss
* multipath delivery probability analysis

---

# 6. Phase-5: Research Platform Maturity

Phase-5 turns AetherNet into a broader **research experimentation framework**.

---

## Wave-49 — Scenario Generator

Goal:

Generate scenario families automatically.

Possible outputs:

* parameterized contact plans
* topology variants
* bandwidth-delay sweeps
* relay timing variants

This makes experiment generation scalable.

---

## Wave-50 — Parameter Sweep Engine

Goal:

Support systematic large-scale experiment execution.

Possible features:

* multiple scenario variants
* multiple policy variants
* multiple tick sizes / end times
* deterministic batch matrix execution

This wave builds on the experiment runner from Wave-34.

---

## Wave-51 — Routing Comparison Framework

Goal:

Standardize routing algorithm comparison.

Expected outputs:

* policy vs policy comparisons
* comparable metrics bundles
* research-grade comparison artifacts
* reproducible experiment matrices

---

## Wave-52 — Paper-Ready Experiment Pipeline

Goal:

Make AetherNet suitable for academic-style reproducible experiments.

Possible capabilities:

* one-command experiment batches
* reproducible result packaging
* chart-ready JSON outputs
* table-friendly metrics summaries
* fixed experiment manifests

---

# 7. Suggested Execution Order

The recommended near-term priority is:

```text
Wave-37 routing policy framework
Wave-38 static routing baseline
Wave-39 contact-aware routing
Wave-40 route scoring engine
Wave-41 CGR-lite
Wave-42 routing metrics
```

This sequence is recommended because:

1. routing abstraction must come first
2. static routing gives a baseline
3. contact awareness introduces time-varying reasoning
4. scoring enables policy sophistication
5. CGR-lite becomes feasible only after the above exist
6. routing metrics are essential for comparing policies

---

# 8. Suggested Milestone Labels

These milestone labels may be useful in PRs, GitHub Projects, or internal planning.

## Milestone A — DTN Transport Complete

Includes:

```text
Phase-1 + Phase-2 + Phase-2.2
```

Status:

```text
completed
```

---

## Milestone B — Routing Framework Ready

Includes:

```text
Wave-37 to Wave-38
```

Outcome:

AetherNet supports pluggable routing policies.

---

## Milestone C — Time-Aware Routing Ready

Includes:

```text
Wave-39 to Wave-41
```

Outcome:

AetherNet supports contact-aware and CGR-lite routing research.

---

## Milestone D — Reliability and Stress Research Ready

Includes:

```text
Wave-43 to Wave-48
```

Outcome:

AetherNet supports congestion, storage, failure, and multipath experiments.

---

## Milestone E — Reproducible Research Platform

Includes:

```text
Wave-49 to Wave-52
```

Outcome:

AetherNet supports large-scale reproducible DTN research workflows.

---

# 9. Recommended Documentation Strategy

Future contributors should keep the following documents updated alongside code changes:

```text
docs/system-sequence.md
docs/architecture-phase-2.md
docs/phase-2-2-whitepaper.md
docs/roadmap.md
```

When moving into Phase-3, it may be useful to also add:

```text
docs/phase-3-routing-whitepaper.md
docs/routing-policy-design.md
```

---

# 10. Recommended Development Rules for Future Waves

For every future Wave:

## Always include

* unit tests
* deterministic behavior
* narrow scope
* module-level documentation updates

## Prefer

* helper-level changes before runtime-level changes
* policy layers before hard-coded logic
* experimentability before cleverness

## Avoid

* large cross-module refactors
* premature optimization
* schema churn without strong reason
* mixing transport changes with routing changes in the same Wave

---

# 11. Summary

AetherNet has already completed the transport and observability foundation needed for serious DTN research.

The next recommended roadmap is:

```text
Phase-3
Routing policy framework
Static routing
Contact-aware routing
Route scoring
CGR-lite
Routing metrics
```

After that, AetherNet should evolve into a richer DTN research environment supporting:

```text
congestion
QoS
storage pressure
failure modeling
opportunistic routing
multipath forwarding
large experiment sweeps
paper-ready reproducible outputs
```

The long-term goal is clear:

> AetherNet should evolve from a deterministic DTN simulator into a modular space-network research platform.

---
