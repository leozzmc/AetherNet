# Release Notes: v0.8-cinematic-demo

## Summary

`v0.8-cinematic-demo` is the first AetherNet release that packages the Phase-6/7 runtime showcase into a recording-ready visual demo.

This release connects the deterministic Python backend, presentation artifact export, and React Flow frontend into a single explainable routing demonstration pipeline.

The main purpose of this release is to make Phase-6 security-aware routing decisions easier to inspect, replay, and present.

---

## Release Focus

This release focuses on:

- deterministic routing decision replay
- security-aware routing comparison
- frontend-ready presentation artifacts
- React Flow visualization
- cinematic Mission Control-style demo mode
- recording and portfolio showcase readiness

---

## Added

### Presentation Layer

Added `aether_phase6_presentation/`, which converts deterministic backend reports into a frontend-ready `presentation.json` artifact.

The artifact includes:

- scenario metadata
- routing decisions
- topology metrics
- React Flow nodes and edges
- story playback script
- narrative and conclusion fields

### Presentation Export Script

Added:

```bash
python scripts/export_presentation_json.py
````

This script generates the payload used by the frontend dashboard.

Recommended usage:

```bash
python scripts/export_presentation_json.py > aethernet-ui/public/presentation.json
```

### React / Next.js Frontend

Added the `aethernet-ui/` frontend for visualizing AetherNet presentation artifacts.

The frontend supports:

* scenario selection
* routing decision panels
* topology metrics panels
* JSON export
* React Flow graph visualization
* story playback controls

### React Flow Visualization

Added graph-based visualization for routing decision traces.

The graph renders:

* decision steps as nodes
* transitions as edges
* status-based styling
* active path highlighting
* story-synchronized playback

### Cinematic Demo Mode

Added URL-driven presentation mode:

```text
http://localhost:3000/?mode=presentation&clean=true&recording=true&scenario=jammed
```

This mode:

* auto-selects the requested scenario
* auto-starts playback
* hides manual controls
* hides debug / inspection panels
* expands the visualization canvas
* keeps the narrative overlay visible

### Demo Documentation

Added public-facing demo documentation, including:

* demo script
* README demo section
* release checklist
* recording-mode instructions

---

## Changed

### Presentation Schema

The presentation schema now supports frontend visualization and cinematic story playback.

Key fields include:

```json
{
  "scenario_id": "jammed",
  "metrics": {
    "nodes": 5,
    "edges": 4,
    "modes": 3,
    "diverged": true
  },
  "decisions": {
    "legacy": "L2",
    "phase6_balanced": "L3",
    "phase6_adaptive": "L3"
  },
  "nodes": [],
  "edges": [],
  "story_script": []
}
```

### Frontend Contract

The frontend now acts as a renderer for backend-generated artifacts.

It does not perform routing inference or recompute routing decisions.

### Demo Packaging

The project now includes a repeatable workflow for generating a presentation artifact and launching a recording-ready frontend demo.

---

## Validation

Backend validation for this release:

```text
make test: 654 passed
```

Recommended local validation:

```bash
make test
python scripts/export_presentation_json.py > aethernet-ui/public/presentation.json
cd aethernet-ui
npm install
npm run dev
```

Then verify:

```text
http://localhost:3000
```

and:

```text
http://localhost:3000/?mode=presentation&clean=true&recording=true&scenario=jammed
```

---

## Demo Scenario

The recommended release demo scenario is:

```text
jammed
```

This scenario is useful because it clearly shows routing divergence:

* legacy routing selects a risky candidate
* Phase-6 selects a safer alternative
* the decision trace is animated step by step
* the narrative overlay explains the routing decision

---

## Current Boundaries

This release does not claim:

* production deployment
* live satellite telemetry ingestion
* real-time operational routing control
* large-scale multi-hop secure route optimization

AetherNet remains a deterministic research and engineering prototype.

---

## Tag

```text
v0.8-cinematic-demo
```

---

## Release Interpretation

`v0.8-cinematic-demo` should be understood as the first public-demo-ready milestone for AetherNet.

It demonstrates that the project can now support:

* reproducible backend routing experiments
* explainable routing decision traces
* frontend artifact-driven visualization
* recording-ready technical demos


