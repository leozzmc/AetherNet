# AetherNet Phase-6 Whitepaper

## Deterministic Security-Aware Decision Layer for Space DTN Systems

---

# 1. Introduction

AetherNet Phase-6 represents the evolution from a deterministic DTN research infrastructure into a **security-aware decision and evaluation system** for space networking environments.

While Phase-5 established a complete:

```text
simulation → experiment → aggregation → comparison → reporting pipeline
````

Phase-6 introduces a new architectural dimension:

> **A deterministic decision layer that evaluates network state and produces explainable routing intelligence**

---

# 2. Phase-5 Recap (Baseline System)

Phase-5 delivers a fully reproducible research pipeline:

```text
simulation
→ experiment harness
→ artifact bundle
→ aggregation
→ research tables
→ snapshot
→ comparison
→ export
→ registry
→ report
```

Key properties:

* deterministic execution
* strict schema validation
* reproducible experiment artifacts
* snapshot-based comparison workflows

This establishes AetherNet as a **research-grade DTN experimentation platform**.

---

# 3. Phase-6 System Position

Phase-6 introduces a **second plane** in the system architecture:

```text
Runtime Plane (Phase 1–5)
    → executes DTN forwarding

Decision Plane (Phase-6)
    → evaluates and recommends routing behavior
```

Important characteristics:

* fully deterministic
* side-effect free (no runtime mutation)
* operates on replayable artifacts
* decoupled from forwarding loop

---

# 4. Phase-6 Core Pipeline

Phase-6 is implemented as a strict, deterministic pipeline:

```text
ScenarioSpec
→ ScenarioGenerator
→ RoutingContext
→ ProbabilisticScorer
→ SecuritySignalBuilder
→ SecurityAwareRoutingEngine
→ Evaluation / Benchmark
```

Each stage transforms structured artifacts without mutating prior state.

---

# 5. Architecture Layers

## 5.1 Scenario Layer

Defines:

* topology
* contact plan
* deterministic traces:

  * reliability degradation
  * adversarial events

---

## 5.2 Context Layer

Extracts:

* time-indexed network state
* candidate links
* observed conditions

Output:

```text
RoutingContext
```

---

## 5.3 Scoring Layer

Computes:

* probabilistic delivery estimates
* penalty-based scoring
* explainable deduction reasons

Output:

```text
RoutingScoreReport
```

---

## 5.4 Security Signal Layer

Transforms scores into:

* severity levels (low / medium / high)
* indicators of compromise
* degraded / jammed / unreliable classifications

Output:

```text
SecuritySignalReport
```

---

## 5.5 Decision Layer

Produces routing recommendations:

```text
preferred
allowed
avoid
```

---

### Decision Contract

Input:

* RoutingContext
* RoutingScoreReport
* SecuritySignalReport

Output:

```text
SecurityAwareRoutingDecision
```

Invariants:

1. coverage: all candidates classified exactly once
2. determinism: identical input → identical output
3. fail-safe: missing data triggers explicit error

---

## 5.6 Evaluation Layer

Executes:

* multi-scenario evaluation
* batch benchmarking
* aggregation via Phase-5 pipeline

---

# 6. Determinism Model (Formal)

For any input:

```text
(ScenarioSpec, Seed, TimeIndex, CandidateSet)
```

The system guarantees identical outputs:

* RoutingContext
* RoutingScoreReport
* SecuritySignalReport
* RoutingDecision

Properties:

1. Seed determinism
2. Execution determinism
3. Serialization determinism
4. Isolation (no cross-layer mutation)

Implementation notes:

* randomness derived via deterministic hashing (e.g., sha256)
* no reliance on global random state
* stable ordering in all exported artifacts

---

# 7. What Phase-6 Does NOT Do (Yet)

To preserve architectural clarity, Phase-6 intentionally excludes:

* runtime routing mutation
* multi-hop path synthesis (graph search)
* real-time adaptive feedback loops
* online learning / training systems

Phase-6 operates strictly as a:

> **deterministic evaluation and decision artifact generator**

---

# 8. System Limitations

* decision layer evaluates candidate links independently
* no end-to-end path optimization yet
* no visualization layer for security signals
* no runtime integration with forwarding engine

---

# 9. Research Impact

Phase-6 enables:

* deterministic evaluation of routing strategies under adversarial conditions
* reproducible space network cybersecurity experiments
* explainable routing decisions (no black-box behavior)
* controlled comparison of probabilistic vs baseline routing

---

# 10. Next Phase: Demo Integration

The next stage (Wave-84~87) focuses on:

* integrating Phase-6 scenarios into demo system
* exposing decision artifacts in runtime demonstrations
* bridging decision plane → runtime plane

---

# 11. Conclusion

Phase-6 transforms AetherNet from:

> a deterministic DTN simulation and research platform

into:

> a deterministic, explainable, security-aware decision system for space networking

This establishes the foundation for:

* intelligent routing evaluation
* space cybersecurity experimentation
* future adaptive and autonomous network systems







