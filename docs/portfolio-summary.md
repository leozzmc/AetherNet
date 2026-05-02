# AetherNet Portfolio Summary

## One-Line Summary

AetherNet is a deterministic, explainable routing decision engine for adversarial DTN and space-like network environments.

---

## Problem

Routing decisions in disrupted or adversarial networks are often difficult to inspect.

In space-like or Delay/Disruption-Tolerant Network (DTN) environments, communication paths may be affected by:

- intermittent connectivity
- delayed contact windows
- degraded links
- jammed or unsafe candidates
- limited operator visibility

When a route is selected or avoided, operators and researchers need more than the final result. They need to understand the decision process.

---

## Solution

AetherNet provides a deterministic simulation and visualization pipeline for explaining routing decisions.

It compares legacy routing behavior with a Phase-6 security-aware decision layer, then converts the result into a replayable presentation artifact. The frontend visualizes the routing decision as an animated Mission Control-style graph.

Instead of treating routing as a black box, AetherNet exposes:

- candidate evaluation
- route divergence
- selected next hops
- decision trace steps
- narrative explanation
- reproducible visual replay

---

## Technical Highlights

### Backend

- Python-based deterministic simulation and routing evaluation
- Phase-6 security-aware routing decision layer
- Legacy vs Phase-6 comparison
- decision trace generation
- benchmark report generation
- frontend-ready `presentation.json` export
- 654 passing tests at `v0.8-cinematic-demo`

### Frontend

- Next.js / React dashboard
- React Flow visualization
- story-driven playback
- Mission Control-style dark interface
- scenario selector
- routing decision and topology metrics panels
- recording-ready presentation mode

---

## Best Demo Scenario

Recommended scenario:

```text
jammed
````

Why this scenario works well:

* legacy routing selects a risky candidate
* Phase-6 selects a safer alternative
* the divergence is visually clear
* the animated story playback explains each decision step

Recording-ready URL:

```text
http://localhost:3000/?mode=presentation&clean=true&recording=true&scenario=jammed
```

---

## Why It Matters

AetherNet demonstrates how infrastructure decisions can be made observable and auditable.

This is relevant to:

* resilient network simulation
* space networking research
* security-aware routing experiments
* infrastructure debugging
* operator-facing explainability
* technical demos for complex decision systems

The key idea is simple:

> make invisible routing decisions visible, traceable, and explainable.

---

## Current Status

Current release:

```text
v0.8-cinematic-demo
```

Completed:

* deterministic backend routing decision pipeline
* presentation artifact export
* cinematic React Flow demo
* recording-ready showcase mode

Not yet included:

* live satellite telemetry ingestion
* production routing deployment
* real-time operational control
* full-scale multi-hop secure path optimization

---

## Future Directions

AetherNet can evolve in two complementary directions.

### Research Direction

Potential research framing:

```text
Explainable Security-Aware Routing for Delay-Tolerant Space Networks
```

Possible extensions:

* multi-hop path synthesis
* contact-plan-based routing evaluation
* adversarial link modeling
* delivery success and latency metrics
* risk-score evaluation
* deterministic replay for network forensics

### Product Direction

Potential product framing:

* mission-control style routing simulator
* network decision visualization platform
* infrastructure debugging tool
* operator-facing explainability layer for automated routing systems

