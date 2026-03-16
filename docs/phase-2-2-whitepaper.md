# AetherNet Phase-2.2 Whitepaper

**AetherNet**
Secure Delay-Tolerant Infrastructure for Space Networks

Phase-2.2 Technical Whitepaper

---

# 1. Introduction

AetherNet is a **research-grade Delay Tolerant Networking (DTN) simulation platform** designed to explore:

* space communication networks
* intermittent connectivity environments
* store-carry-forward routing
* fragmentation and reassembly
* reliability mechanisms
* contact-aware routing

The system models the **bundle lifecycle of deep-space communication networks** such as:

```
Moon relay networks
Mars communication infrastructure
satellite mesh networks
deep-space DTN protocols
```

The simulator provides a deterministic environment for experimentation with:

```
bundle transport
fragmentation
custody transfer
contact windows
routing algorithms
network reliability
```

---

# 2. Project Phases

AetherNet is developed in **incremental Waves grouped into Phases**.

| Phase     | Focus                                |
| --------- | ------------------------------------ |
| Phase-1   | Core DTN simulator                   |
| Phase-2   | Transport reliability features       |
| Phase-2.2 | Observability + experiment artifacts |
| Phase-3   | Contact-aware routing research       |
| Phase-4   | Advanced DTN reliability research    |

---

# 3. Phase-2 Overview

Phase-2 expanded the simulator to support **realistic DTN transport behavior**.

Major additions:

```
bundle fragmentation
fragment reassembly
fragment buffers
priority queue scheduling
store-carry-forward persistence
bundle lifecycle metrics
```

This created a **complete DTN bundle transport pipeline**.

---

# 4. Phase-2 Transport Pipeline

The bundle lifecycle in Phase-2:

```
Bundle Created
↓
Fragmentation
↓
Priority Queue
↓
DTN Store
↓
Contact Window Opens
↓
Forwarding Hop
↓
Relay Storage
↓
Next Contact Window
↓
Destination Reception
↓
Fragment Reassembly
↓
Bundle Delivered
```

This models **real DTN behavior in intermittent networks**.

---

# 5. Core Modules Implemented

The following modules were implemented or stabilized during Phase-2.

---

## Simulator

Location:

```
sim/
```

Responsibilities:

```
simulation clock
scenario execution
contact window scheduling
hop forwarding
bundle lifecycle tracking
```

Core component:

```
sim/simulator.py
```

---

## Routing Layer

Location:

```
router/
```

Responsibilities:

```
bundle forwarding
routing decisions
next-hop selection
bundle state transitions
```

Bundle states:

```
QUEUED
STORED
FORWARDING
DELIVERED
EXPIRED
FAILED
```

---

## Fragmentation

Location:

```
protocol/fragmentation.py
```

Responsibilities:

```
split bundles into deterministic fragments
attach fragment metadata
maintain fragment ordering
```

Fragment metadata:

```
original_bundle_id
fragment_index
total_fragments
```

---

## Reassembly

Location:

```
protocol/reassembly.py
```

Responsibilities:

```
validate fragment completeness
reconstruct original bundle
verify metadata integrity
```

Key APIs:

```
can_reassemble()
reassemble_bundle()
```

---

## Reassembly Buffer

Location:

```
protocol/reassembly_buffer.py
```

Purpose:

Temporarily stores fragments until a complete fragment set is available.

Structure:

```
bundle_id → fragment set
```

Example:

```
science-001
 ├ frag-0
 ├ frag-1
 └ frag-2
```

---

## Priority Queue

Location:

```
bundle_queue/priority_queue.py
```

Implements **strict priority scheduling**.

Example priority order:

```
telemetry > science
```

---

## DTN Store

Location:

```
store/store.py
```

Implements **store-carry-forward persistence**.

Responsibilities:

```
store bundles during disconnections
retrieve bundles during contact windows
simulate node storage
```

---

# 6. Observability Layer

Phase-2 introduced a structured **network observability system**.

Location:

```
metrics/
report/
analysis/
```

Capabilities:

```
bundle lifecycle metrics
delivery latency tracking
forwarding hop tracking
fragment counts
experiment reporting
```

Reports are written to:

```
artifacts/reports/
```

---

# 7. Phase-2.2 Observability Extension

Phase-2.2 introduced **structured experiment artifacts**.

Purpose:

```
export experiment results
enable visualization pipelines
enable reproducible research outputs
```

Key capability:

```
export_experiment_artifacts()
```

Artifacts include:

```
experiment metrics
bundle timelines
delivery statistics
forwarding counts
```

Output format:

```
JSON artifacts
```

Example directory:

```
artifacts/
  runs/
    run_001_metrics.json
    run_001_timelines.json
```

These artifacts enable visualization using:

```
Jupyter Notebook
Python analysis scripts
research dashboards
```

---

# 8. Repository Structure

Current repository layout:

```
sim/
router/
protocol/
store/
bundle_queue/
metrics/
report/
analysis/
tests/
docs/
```

Each module is intentionally **loosely coupled** to enable future research extensions.

---

# 9. System Properties

AetherNet models several core DTN properties.

---

## Store-Carry-Forward

Bundles survive network disconnections.

---

## Contact-Aware Transmission

Bundles transmit only during valid contact windows.

---

## Fragmented Transport

Large bundles are split across constrained links.

---

## Deterministic Simulation

Experiments are reproducible.

---

## Research Observability

Simulation results can be exported for analysis.

---

# 10. Phase-3 Roadmap

After completion of Phase-2.2, AetherNet transitions to **routing research**.

---

## Wave-37

Contact Plan infrastructure.

Implementation:

```
contact_plan.py
```

Capabilities:

```
scheduled link windows
time-varying connectivity graphs
```

---

## Wave-38

Graph construction for routing.

System builds a **time-varying contact graph**.

Nodes:

```
network nodes
```

Edges:

```
contact windows
```

---

## Wave-39

Contact Graph Routing (CGR) implementation.

Capabilities:

```
predict future connectivity
compute optimal bundle routes
delay-aware routing decisions
```

---

## Wave-40

Routing strategy comparison.

Evaluate algorithms:

```
static routing
contact graph routing
epidemic routing
spray and wait
```

Metrics:

```
delivery ratio
latency
buffer utilization
network congestion
```

---

## Wave-41+

Advanced DTN reliability.

Potential features:

```
custody transfer
fragment retransmission
buffer congestion control
priority aging
adaptive routing
```

---

# 11. Long-Term Research Vision

AetherNet aims to become a **space networking research platform**.

Future exploration areas:

```
interplanetary internet protocols
deep space routing
lunar relay networks
mars communication systems
satellite mesh networks
```

---

# 12. Summary

After Phase-2.2 completion, AetherNet supports a full DTN transport lifecycle:

```
bundle creation
fragmentation
priority scheduling
store-carry-forward routing
multi-hop forwarding
fragment buffering
bundle reassembly
delivery metrics
experiment artifact export
```

The system is now ready for **Phase-3 routing algorithm research**.

---