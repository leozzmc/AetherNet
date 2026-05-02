## 🚀 AetherNet Phase-6 Cinematic Demo

AetherNet is an **Explainable Routing Decision Engine** designed for adversarial space network environments (DTN). 

This demo visualizes the deterministic decision-making process of the Phase-6 security engine compared to legacy routing algorithms. It transforms opaque routing logs into a traceable, animated, and highly visual "Mission Control" experience.

### 🌟 What this demo shows:
- **Scenario-Driven Simulation**: Watch how the network reacts to `clean`, `jammed`, or `degraded` link conditions.
- **Explainable Tracing**: Every step of the routing algorithm is mapped to a visual graph.
- **Path Divergence**: Clearly see where the Legacy system fails (Red) and how the Phase-6 engine secures the packet (Green).

### 🛠️ How to run the Demo Locally

**1. Generate the deterministic payload (Backend)**
Make sure your Python environment is set up, then run the simulation benchmark to export the UI payload:
```bash
python scripts/export_presentation_json.py > aethernet-ui/public/presentation.json
```

**2. Start the Mission Control UI (Frontend)**

```bash
cd aethernet-ui
npm install
npm run dev
```

### 🎬 Presentation & Recording Modes
The UI supports URL parameters to create a distraction-free environment for presentations and screen recordings.

- **Standard Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Cinematic Recording Mode**: [http://localhost:3000/?mode=presentation&clean=true&recording=true&scenario=jammed](http://localhost:3000/?mode=presentation&clean=true&recording=true&scenario=jammed)
  *(This mode auto-starts the animation loop, hides manual controls, and expands the graph to full screen.)*
```







