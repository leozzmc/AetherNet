# AetherNet Phase-6 Whitepaper

## Deterministic Security-Aware Decision and Demo Layer for Space DTN Systems

---

# 1. Introduction

AetherNet Phase-6 extends the project from a deterministic DTN research infrastructure into a **security-aware decision and presentation system** for space-like networking environments.

Phase-5 established a complete deterministic research pipeline:

```text
simulation → experiment → aggregation → comparison → reporting
````

Phase-6 adds a new architectural dimension:

> a deterministic decision layer that evaluates network state, produces explainable routing decisions, and exposes them through demo-ready artifacts and reports.

---

# 2. Phase-5 Baseline

Phase-5 provides:

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
* structured report generation

This established AetherNet as a research-grade DTN experimentation platform.

---

# 3. Phase-6 System Position

Phase-6 introduces a **Decision Plane** and a **Presentation Plane**, while keeping the forwarding runtime separate.

```text
Runtime Plane (Phase 1–5)
    → executes DTN forwarding

Decision Plane (Phase-6 Core)
    → evaluates candidate links and produces deterministic decision artifacts

Presentation Plane (Phase-6 Demo)
    → renders artifacts into human-readable reports and comparisons
```

Important:

* Phase-6 is deterministic
* Phase-6 is decoupled from runtime forwarding
* Phase-6 does not yet inject decisions into the live forwarding loop

---

# 4. Phase-6 Core Pipeline

```text
ScenarioSpec
→ ScenarioGenerator
→ RoutingContext
→ ProbabilisticScorer
→ SecuritySignalBuilder
→ SecurityAwareRoutingEngine
→ Evaluation / Benchmark
```

This pipeline is fully implemented.

---

# 5. Phase-6 Demo Pipeline

```text
Phase6ScenarioRegistry
→ Phase6DemoArtifactBuilder
→ Phase6DemoReportBuilder
→ Phase6DemoBridge
→ Phase6ComparisonBuilder
```

This pipeline makes Phase-6 observable through deterministic demo artifacts and plain-text reports.

---

# 6. Architecture Layers

## 6.1 Scenario Layer

Defines:

* deterministic topology dimensions
* reliability traces
* adversarial traces

## 6.2 Context Layer

Builds a time-indexed routing snapshot:

* candidate links
* observed conditions
* network observation state

Output:

```text
RoutingContext
```

## 6.3 Scoring Layer

Computes:

* penalty-based link scoring
* estimated success probabilities
* structured reasons

Output:

```text
RoutingScoreReport
```

## 6.4 Security Signal Layer

Transforms observations and scores into:

* severity tiers
* link threat indicators
* node compromise indicators

Output:

```text
SecuritySignalReport
```

## 6.5 Decision Layer

Produces deterministic link classifications:

* preferred
* allowed
* avoid

Output:

```text
SecurityAwareRoutingDecision
```

## 6.6 Evaluation and Benchmark Layer

Supports:

* multi-case evaluation
* conservative aggregation
* benchmark pack execution

## 6.7 Presentation Layer

Supports:

* canonical demo scenarios
* artifact bundle generation
* human-readable reports
* scenario-to-scenario comparison

---

# 7. Determinism Model

For any fixed input tuple:

```text
(ScenarioSpec, Seed, TimeIndex, CandidateSet)
```

Phase-6 guarantees identical outputs:

* RoutingContext
* RoutingScoreReport
* SecuritySignalReport
* SecurityAwareRoutingDecision
* demo artifact bundle
* demo report
* comparison report

Properties:

1. Seed determinism
2. Execution determinism
3. Serialization determinism
4. Isolation (no mutation leaks across exported artifacts)

---

# 8. Decision Contract

Input:

* RoutingContext
* RoutingScoreReport
* SecuritySignalReport

Output:

* SecurityAwareRoutingDecision

Invariants:

1. every candidate link must be covered exactly once
2. missing score/signal coverage fails explicitly
3. identical inputs produce identical decisions
4. no silent fallback to “safe” defaults

---

# 9. What Phase-6 Does Not Do

Phase-6 intentionally does **not** yet provide:

* runtime forwarding-loop integration
* multi-hop graph/path synthesis
* online learning or training
* dashboard / visualization UI

These remain future work.

---

# 10. Research and Engineering Impact

Phase-6 enables:

* deterministic adversarial DTN evaluation
* explainable routing decision artifacts
* reproducible security-aware scenario comparison
* benchmark-ready and demo-visible outputs

---

# 11. Conclusion

Phase-6 transforms AetherNet from:

> a deterministic DTN research simulator

into:

> a deterministic, explainable, security-aware decision and demo system for space networking research

The remaining major gap is runtime integration, not core decision functionality.
