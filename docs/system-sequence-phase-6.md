# 1. End-to-End Lifecycle (Phase-6)

```mermaid
sequenceDiagram
    participant Simulator
    participant RoutingPolicy
    participant IntelligenceLayer
    participant SecurityLayer
    participant Storage
    participant ExperimentHarness
    participant Aggregation
    participant Snapshot
    participant Registry
    participant Report

    Simulator->>RoutingPolicy: evaluate routing
    RoutingPolicy->>IntelligenceLayer: adaptive decision
    IntelligenceLayer->>SecurityLayer: risk evaluation
    SecurityLayer-->>RoutingPolicy: allow / deny / adjust

    RoutingPolicy->>Storage: forward or hold bundle

    ExperimentHarness->>Simulator: run experiments
    Simulator-->>ExperimentHarness: results

    ExperimentHarness->>Aggregation: aggregate results
    Aggregation->>Snapshot: build snapshot

    Snapshot->>Registry: register snapshot
    Registry->>Report: provide metadata

    Report->>Report: generate research report
```

---

# 2. Layered Architecture

## Core Layers

```
Simulation Layer
→ Routing Layer
→ Intelligence Layer (NEW)
→ Security Layer (NEW)
→ Research Pipeline Layer
→ Report Layer
```

---

# 3. Key Transitions from Phase-5

### Before

- static routing
- deterministic evaluation

### After

- adaptive routing
- policy-driven decisions
- security-aware behavior

---

# 4. Determinism Flow

Even with adaptive features:

```
seeded randomness
→ controlled execution
→ reproducible results
→ comparable outputs
```

---

# 5. Research Workflow

```
define scenario
→ run experiment
→ generate snapshot
→ compare snapshots
→ export comparison
→ generate report
→ analyze results
```

---
