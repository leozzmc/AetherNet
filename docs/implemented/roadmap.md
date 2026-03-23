# AetherNet Roadmap

**AetherNet**  
A Secure Delay-Tolerant Distributed Infrastructure Prototype for Space Networks

This roadmap describes the evolution of AetherNet from a **Phase-1 DTN transport simulator** into a **research-grade space networking platform**.

This document is written primarily for:

- new engineers onboarding to the repository
- future AI-agent / ChatGPT handoff sessions
- contributors planning the next Wave safely
- research users trying to understand what is already implemented vs. what remains future work

---

# 1. Current Status

AetherNet has completed:

```text
Phase-1   core DTN simulator
Phase-2   transport reliability baseline
Phase-2.2 observability and research tooling
Phase-3   routing intelligence baseline
Phase-4   stress / resilience baseline
```

Current system capabilities include:

- deterministic scenario execution
- contact-window-driven forwarding
- store-carry-forward persistence
- strict priority queueing
- deterministic fragmentation and reassembly
- partial transmission helper
- fragment retransmission helper
- fragment garbage collection
- custody transfer baseline
- contact plan parsing
- experiment runner
- reporting and comparison
- visualization spec generation
- deterministic artifact export
- pluggable routing policies
- static routing baseline
- contact-aware routing
- route scoring and multi-candidate ranking
- CGR-lite bounded future-contact reasoning
- routing decision observability and routing metrics
- congestion-control baseline with finite storage
- QoS baseline with priority aging
- storage-pressure modeling with eviction policy abstraction
- opportunistic hold-vs-forward routing baseline
- deterministic failure / partition modeling
- bounded multi-path candidate selection

AetherNet is now beyond transport realism.  
It has entered the stage of **routing, resilience, and storage-pressure experimentation**.

---

# 2. Guiding Principles

All future development should preserve the following properties.

## Determinism

AetherNet is first and foremost a **deterministic simulator**.
The same inputs should produce the same outputs.

## Incremental Development

Each Wave should:

- be small
- have clear boundaries
- include tests
- avoid unnecessary refactors

## Additive Architecture

New features should prefer:

- new helper modules
- policy layers
- clear interfaces
- low coupling
- backward-compatible wrappers over API breakage

## Research Utility

Every major addition should improve one or more of:

- realism
- experimentability
- observability
- reproducibility
- policy comparability

---

# 3. Completed Roadmap

## Phase-1: Core DTN Simulator

Completed baseline:

- scenario system
- simulator clock and tick execution
- contact window scheduling
- store-carry-forward
- strict priority queue
- multi-hop forwarding
- baseline reporting

---

## Phase-2: Transport Reliability

Completed Waves:

### Wave-26 — Contact-Aware Fragmentation

Added contact-capacity-aware fragmentation planning.

### Wave-27 — Partial Contact Transmission

Added helper logic for splitting a bundle into:

- transmitted part
- residual part

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

- batch results
- aggregate comparisons
- visualization specs
- manifests

---

## Phase-3: Routing Layer

Phase-3 delivered the **routing brain** of AetherNet.

What Phase-3 added:

- policy abstraction
- baseline route selection
- contact-aware next-hop gating
- multi-candidate scoring
- bounded future-contact reasoning
- routing observability and comparison primitives

### Wave-37 — Routing Policy Framework

Delivered:

- pluggable routing policy abstraction
- backward-compatible default routing behavior
- router-level policy injection
- policy-focused test coverage

Primary outcome:

```text
AetherRouter no longer hardcodes one routing behavior.
```

### Wave-38 — Static Routing Baseline

Delivered:

- deterministic static route lookup baseline
- explicit no-route semantics
- destination-arrival semantics
- stable baseline for later policy comparison

Primary outcome:

```text
AetherNet gained a debuggable reference routing baseline.
```

### Wave-39 — Contact-Aware Routing

Delivered:

- routing decisions gated by current contact availability
- explicit contact-blocked behavior
- safe distinction between “route exists” and “route usable now”

Primary outcome:

```text
AetherNet became contact-aware at routing-decision time.
```

### Wave-40 — Route Scoring Engine

Delivered:

- deterministic candidate ranking
- score-based next-hop selection
- lexical tie-breaks for stable ordering
- scored multi-candidate routing baseline

Primary outcome:

```text
AetherNet can rank multiple candidate next hops instead of using only one hardwired choice.
```

### Wave-41 — CGR-lite

Delivered:

- bounded future-contact reasoning
- two-hop earliest-arrival approximation
- future-path preference without full graph-engine complexity
- clean separation between policy preference and current forwarding feasibility

Primary outcome:

```text
AetherNet supports bounded future-contact routing research.
```

### Wave-42 — Routing Metrics

Delivered:

- RoutingDecision abstraction
- policy introspection via decision reasons
- RoutingMetricsCollector
- deterministic routing-observability baseline

Primary outcome:

```text
Routing policies can now be compared by decision reason, not just by top-hop output.
```

---

## Phase-4: Advanced DTN Stress / Resilience Baseline

Phase-4 extends AetherNet from “intelligent routing” into “routing under stress, scarcity, and disruption”.

### Wave-43 — Congestion Control

Delivered:

- finite node storage capacity baseline
- deterministic overflow drop behavior
- congestion metrics for store pressure

Primary outcome:

```text
AetherNet no longer assumes infinite storage.
```

### Wave-44 — Priority / QoS

Delivered:

- differentiated service-class priority baseline
- deterministic priority aging
- pure QoS helper logic without mutating bundle state

Primary outcome:

```text
AetherNet can model starvation mitigation and service-class differentiation.
```

### Wave-45 — Storage Pressure Modeling

Delivered:

- eviction policy abstraction
- DropLowestPriorityPolicy baseline
- DropOldestPolicy baseline
- storage-pressure metrics such as peak occupancy and dropped bytes

Primary outcome:

```text
AetherNet can compare deterministic storage-eviction strategies.
```

### Wave-46 — Opportunistic Routing

Delivered:

- bounded hold-vs-forward opportunistic policy
- deterministic hold window
- explicit “hold for better near-future contact” behavior

Primary outcome:

```text
AetherNet can prefer strategic waiting over immediate forwarding.
```

### Wave-47 — Failure / Partition Modeling

Delivered:

- node outage windows
- link failure windows
- runtime forwarding gate for outage / partition simulation
- deterministic recovery semantics after failure windows end

Primary outcome:

```text
AetherNet can model temporary partitions and recovery without polluting routing-policy logic.
```

### Wave-48 — Multi-Path Forwarding Baseline

Delivered:

- deterministic top-k next-hop candidate selection
- bounded multi-path path-diversity baseline
- backward-compatible single-path API fallback
- no uncontrolled replication

Primary outcome:

```text
AetherNet can reason about multiple current viable paths without yet performing full replicated transmission.
```

---

# 4. Current Architectural Milestone

AetherNet has now reached the following milestone state:

```text
Milestone A — DTN Transport Complete           ✅
Milestone B — Routing Framework Ready          ✅
Milestone C — Time-Aware Routing Ready         ✅
Milestone D — Stress / Resilience Baseline     ✅
```

The next major frontier is **Phase-5: research platform maturity**.

---

# 5. Next Recommended Roadmap

## Phase-5: Research Platform Maturity

Phase-5 should turn the current routing / resilience core into a broader **experiment framework**.

### Wave-49 — Scenario Generator

Goal:

Generate scenario families automatically.

Possible outputs:

- parameterized contact plans
- topology variants
- bandwidth-delay sweeps
- relay timing variants
- failure-window variants
- storage-pressure variants

Why this matters:

The platform now has enough behaviors to justify systematic scenario generation instead of hand-written single scenarios only.

---

### Wave-50 — Parameter Sweep Engine

Goal:

Support systematic large-scale experiment execution.

Possible features:

- scenario matrices
- policy matrices
- hold-window / max-path sweeps
- storage-capacity sweeps
- failure-window sweeps
- deterministic batch matrix execution

This wave should build on the existing experiment runner rather than replace it.

---

### Wave-51 — Routing Comparison Framework

Goal:

Standardize routing algorithm comparison.

Expected outputs:

- policy vs policy comparisons
- comparable metrics bundles
- research-grade comparison artifacts
- reproducible experiment manifests

This wave should build on Wave-42 routing metrics rather than invent a separate observability path.

---

### Wave-52 — Paper-Ready Experiment Pipeline

Goal:

Make AetherNet suitable for academic-style reproducible experiments.

Possible capabilities:

- one-command experiment batches
- reproducible result packaging
- chart-ready JSON outputs
- table-friendly metrics summaries
- fixed experiment manifests
- benchmark scenario packs

---

# 6. Suggested Execution Order

Recommended near-term priority:

```text
Wave-49 scenario generator
Wave-50 parameter sweep engine
Wave-51 routing comparison framework
Wave-52 paper-ready experiment pipeline
```

This is the recommended order because:

1. the routing / resilience core is already implemented
2. the next bottleneck is experiment scalability
3. comparison value comes from repeated scenario execution, not just more policies
4. paper-ready workflows should build on already-stable experiment and comparison primitives

---

# 7. Suggested Milestone Labels

These milestone labels are useful in PRs, GitHub Projects, release notes, or handoff sessions.

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

Status:

```text
completed
```

---

## Milestone C — Time-Aware Routing Ready

Includes:

```text
Wave-39 to Wave-41
```

Outcome:

AetherNet supports contact-aware and CGR-lite routing research.

Status:

```text
completed
```

---

## Milestone D — Routing Observability Ready

Includes:

```text
Wave-42
```

Outcome:

Routing policies expose deterministic decision reasons and metrics.

Status:

```text
completed
```

---

## Milestone E — Stress / Resilience Baseline Ready

Includes:

```text
Wave-43 to Wave-48
```

Outcome:

AetherNet supports congestion, QoS, storage pressure, opportunistic hold-vs-forward, deterministic failure modeling, and bounded multi-path path diversity.

Status:

```text
completed
```

---

## Milestone F — Reproducible Research Platform

Includes:

```text
Wave-49 to Wave-52
```

Outcome:

AetherNet supports scalable experiment generation, systematic sweeps, comparison artifacts, and paper-ready reproducibility.

Status:

```text
planned
```

---

# 8. Recommended Documentation Strategy

The following documents should remain synchronized with code changes:

```text
docs/system-sequence.md
docs/architecture-phase-2.md
docs/phase-2-whitepaper.md
docs/phase-2-2-whitepaper.md
docs/phase-3-4-whitepaper.md
docs/roadmap.md
README.md
```

Recommended documentation roles:

- `README.md` → high-level repository entry point
- `docs/roadmap.md` → wave sequencing, milestones, next priorities
- `docs/system-sequence.md` → runtime lifecycle and execution path
- `docs/phase-3-4-whitepaper.md` → handoff-grade architecture + completed routing / resilience summary

---

# 9. Recommended Development Rules for Future Waves

For every future Wave:

## Always include

- unit tests
- deterministic behavior
- narrow scope
- module-level documentation updates
- explicit backward-compatibility notes

## Prefer

- helper-level changes before runtime-level changes
- additive APIs before interface breakage
- observability before complexity
- policy comparison value over novelty for its own sake

## Avoid

- large cross-module refactors
- premature optimization
- schema churn without strong reason
- mixing transport changes with routing changes in the same Wave
- introducing probabilistic behavior before the deterministic baseline is fully documented

---

# 10. Summary

AetherNet has completed the transition from **transport baseline** into a **routing + resilience experimentation core**.

The system now supports:

```text
fragmentation / reassembly
store-carry-forward
static routing
contact-aware routing
route scoring
CGR-lite
routing observability
finite storage
QoS aging
storage pressure modeling
opportunistic hold-vs-forward
failure / partition modeling
bounded multi-path candidate selection
```

The next recommended roadmap is:

```text
Phase-5
scenario generation
parameter sweeps
routing comparison framework
paper-ready experiment pipeline
```

The long-term goal remains clear:

> AetherNet should evolve from a deterministic DTN simulator into a modular space-network research platform.
