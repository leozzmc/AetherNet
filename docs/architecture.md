# AetherNet Architecture

AetherNet is a **deterministic Delay-Tolerant Networking (DTN) system** designed for:

- space-like intermittent connectivity
- long propagation delays
- adversarial and degraded network conditions
- routing policy experimentation and evaluation

It evolves from a simulator into a:

> **deterministic, security-aware routing decision and control system**

---

## 1. High-Level Architecture

AetherNet is composed of three primary planes:

```text
Runtime Plane
    → executes DTN simulation and forwarding

Decision Plane
    → evaluates network state and produces routing decisions

Runtime Control & Presentation Plane
    → applies decisions, adapts behavior, and generates outputs
````

---

## 2. System Topology (Reference)

```mermaid
graph LR
    lunar-node --> leo-relay
    lunar-node --> relay-a
    relay-a --> relay-b
    relay-b --> ground-station
    leo-relay --> ground-station
```

This topology models:

* Earth ↔ LEO relay
* relay mesh
* ground station endpoint

---

## 3. Runtime Plane (Phase-1~5)

The runtime plane simulates DTN behavior:

### Responsibilities

* bundle injection and propagation
* store-carry-forward persistence
* contact-aware forwarding
* queue scheduling and prioritization
* congestion and eviction
* failure and partition modeling

---

### Core Modules

```text
sim/          → simulation orchestration
router/       → routing policies and forwarding decisions
bundle_queue/ → scheduling and priority handling
store/        → persistence and bundle lifecycle
```

---

### Execution Flow

```mermaid
sequenceDiagram
    participant Scenario
    participant Simulator
    participant Store
    participant Policy

    Scenario->>Simulator: inject bundle
    Simulator->>Store: enqueue bundle

    Simulator->>Policy: request next hop
    Policy-->>Simulator: next hop / hold

    alt forward
        Simulator->>Simulator: transmit bundle
    else hold
        Simulator->>Store: persist bundle
    end
```

---

## 4. Decision Plane (Phase-6)

The decision plane evaluates candidate links at a given time snapshot.

---

### Core Pipeline

```mermaid
sequenceDiagram
    participant Context as RoutingContext
    participant Scorer as ProbabilisticScorer
    participant Signals as SecuritySignalBuilder
    participant Engine as SecurityAwareRoutingEngine

    Context->>Scorer: evaluate candidates
    Scorer-->>Signals: RoutingScoreReport

    Signals->>Signals: build threat indicators
    Signals-->>Engine: SecuritySignalReport

    Engine->>Engine: classify candidates
    Engine-->>User: SecurityAwareRoutingDecision
```

---

### Output Model

Each candidate link is classified as:

```text
preferred → safe / optimal
allowed   → usable but degraded
avoid     → unsafe / adversarial
```

---

### Design Properties

* deterministic (seed-based)
* complete (all candidates classified)
* explainable (decision traceable)
* replayable (artifact-based)

---

## 5. Runtime Control & Adaptive Layer (Phase-7)

This layer bridges decision outputs into runtime-like behavior.

---

### Components

```text
Phase6DecisionAdapter
AdaptivePhase6Adapter
RoutingMetricsCollector
```

---

### Flow

```mermaid
sequenceDiagram
    participant Context
    participant Adapter
    participant Adaptive
    participant Metrics

    Context->>Adapter: compute decisions
    Adapter-->>Adaptive: safe candidates + decision map

    Adaptive->>Adaptive: apply runtime mode
    Adaptive-->>Metrics: final candidates
```

---

### Adaptive Modes

#### Conservative

* keep only preferred links if available
* fallback to allowed if necessary

---

#### Balanced

* preferred first, then allowed
* avoid removed

---

#### Aggressive

* preserve original candidate order
* remove only avoid links

---

## 6. Policy Comparison Layer (Wave-93)

Enables deterministic comparison across runtime strategies.

---

### Components

```text
PolicyComparisonCase
PolicyComparisonRunner
PolicyComparisonResult
```

---

### Flow

```mermaid
sequenceDiagram
    participant Case
    participant Runner
    participant Adapter
    participant Adaptive

    Case->>Runner: run_case()

    Runner->>Adapter: baseline decision
    Runner->>Adaptive: conservative
    Runner->>Adaptive: balanced
    Runner->>Adaptive: aggressive

    Runner-->>User: comparison result
```

---

## 7. Presentation / Showcase Layer (Wave-94~95)

Transforms comparison results into human-readable artifacts.

---

### Components

```text
PolicyShowcaseBuilder
PolicyShowcaseReport
scripts/run_phase6_showcase.py
```

---

### Flow

```mermaid
sequenceDiagram
    participant Runner
    participant Builder
    participant CLI

    Runner-->>Builder: comparison result
    Builder->>Builder: compute differences
    Builder-->>CLI: report
    CLI-->>User: print text
```

---

## 8. End-to-End System Flow

```mermaid
flowchart TB
    SCEN[Scenario]
    SIM[Simulation]
    CONTEXT[Routing Context]
    SCORE[Scoring]
    SIGNAL[Security Signals]
    DECISION[Decision]
    ADAPTER[Runtime Adapter]
    ADAPTIVE[Adaptive Policy]
    COMP[Comparison]
    SHOW[Showcase]

    SCEN --> SIM --> CONTEXT
    CONTEXT --> SCORE --> SIGNAL --> DECISION
    DECISION --> ADAPTER --> ADAPTIVE
    ADAPTIVE --> COMP --> SHOW
```

---

## 9. Deterministic Design Guarantees

AetherNet enforces:

* identical inputs → identical outputs
* no hidden state across runs
* stable ordering and serialization
* deterministic adaptive behavior
* no randomness in runtime policy layer

---

## 10. System Boundaries

AetherNet currently does NOT:

* integrate adaptive policy into full simulation loop by default
* compute multi-hop secure path synthesis
* include visualization/dashboard UI
* perform online learning or reinforcement learning

---

## 11. Evolution Path

```text
Simulator (Phase-1~5)
→ Decision System (Phase-6)
→ Runtime Control Layer (Phase-7)
→ Live Adaptive Routing System (Next)
```

---

## 12. Key Insight

AetherNet is not just a simulator.

It is:

> a deterministic system that can evaluate, control, and explain routing decisions under adversarial DTN conditions.


