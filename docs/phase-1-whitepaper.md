# AetherNet Technical Whitepaper v0.1

### Phase-1 Architecture and DTN Simulation Platform

Author: Kevin Liu
Project: **AetherNet**
Version: 0.1
Status: **Phase-1 Complete**

---

# 1. Abstract

Space communication networks operate under extreme conditions that fundamentally differ from terrestrial Internet environments. Long propagation delays, intermittent connectivity, and limited bandwidth render traditional TCP/IP-based networking unsuitable for deep-space missions.

This paper presents **AetherNet**, a prototype delay-tolerant networking (DTN) infrastructure simulator designed to explore **store-carry-forward communication architectures** for space environments.

AetherNet models:

* contact-aware routing
* strict priority scheduling
* bundle lifecycle tracking
* deterministic event-driven simulation

The current implementation (Phase-1) provides a **fully testable DTN simulation framework** capable of reproducing key networking behaviors observed in space communication systems such as **Lunar relay networks**.

---

# 2. Background

Traditional Internet protocols assume:

* continuous connectivity
* low latency
* symmetric bandwidth

However, space networks violate these assumptions.

Typical characteristics include:

| Characteristic                | Example                 |
| ----------------------------- | ----------------------- |
| High latency                  | Earth-Moon ~1.3s        |
| Intermittent connectivity     | orbital contact windows |
| Asymmetric bandwidth          | uplink vs downlink      |
| Store-and-forward requirement | relay satellites        |

To address these constraints, **Delay-Tolerant Networking (DTN)** was developed.

DTN introduces the **Bundle Protocol** and **store-carry-forward communication model**.

Instead of dropping packets when links fail, intermediate nodes **store bundles until a future contact window becomes available**.

---

# 3. AetherNet Objectives

The AetherNet project explores the following research questions:

1. How should routing behave under intermittent connectivity?
2. How should nodes prioritize mission-critical telemetry?
3. How should bundles persist across long disconnections?
4. How can DTN systems be simulated deterministically for research?

AetherNet aims to provide a **modular experimental platform** for these questions.

---

# 4. System Overview

AetherNet is implemented as a **deterministic event-driven simulation platform**.

Instead of relying on real time, the simulator advances through **virtual ticks**.

Example timeline:

```
tick 0 → tick 1 → tick 2 → tick 3 ...
```

At every tick the simulator evaluates:

* contact window status
* queue ordering
* forwarding opportunities
* bundle expiration

---

# 5. Reference Deployment Scenario: LunarNet

To validate the architecture, AetherNet uses a simplified **three-node topology**.

```
Moon Node → LEO Relay → Earth Ground Station
```

Roles:

| Node           | Function                            |
| -------------- | ----------------------------------- |
| Lunar Node     | generates bundles                   |
| LEO Relay      | stores bundles during disconnection |
| Ground Station | final destination                   |

This topology mirrors real **Lunar relay concepts** currently explored by space agencies.

---

# 6. Core Architectural Components

AetherNet is structured into modular subsystems.

## 6.1 Simulator Engine

Location:

```
sim/
```

Responsibilities:

* virtual clock management
* event scheduling
* forwarding evaluation
* report generation

The simulator ensures **deterministic execution**, allowing reliable testing.

---

## 6.2 Contact Manager

Location:

```
router/contact_manager.py
```

The contact manager determines **link availability** between nodes.

Example contact schedule:

```
Moon → LEO : ticks 5-10
LEO → Earth : ticks 15-20
```

Bundles may only be forwarded during active windows.

---

## 6.3 Strict Priority Queue

Location:

```
bundle_queue/
```

Bundles are scheduled using **strict priority ordering**.

Priority classes:

| Bundle Type | Priority |
| ----------- | -------- |
| telemetry   | high     |
| science     | low      |

Guarantee:

```
telemetry always forwarded before science
```

FIFO ordering is preserved within the same priority class.

---

## 6.4 DTN Store

Location:

```
store/
```

The DTN store implements the **store-carry-forward paradigm**.

When a link is unavailable:

```
bundle → stored
```

When the link becomes available:

```
bundle → forwarded
```

Additional behaviors include:

* TTL expiration
* retention cleanup
* persistent metadata storage

---

## 6.5 Metrics and Reporting

Location:

```
metrics/
```

AetherNet tracks bundle lifecycle events including:

```
CREATED
QUEUED
FORWARDED
STORED
DELIVERED
EXPIRED
```

Simulation results are exported as structured JSON reports.

Metrics include:

* delivery span
* storage duration
* forwarding order
* bundle outcomes

Reports are written to:

```
artifacts/reports/
```

---

# 7. Simulation Scenarios

Phase-1 includes three validated scenarios.

## default_multihop

Demonstrates normal multi-hop delivery.

Expected behavior:

* relay temporarily stores bundles
* telemetry delivered before science

---

## delayed_delivery

Demonstrates long disconnection periods.

Validates:

```
store-carry-forward behavior
```

---

## expiry_before_contact

Simulates bundle expiration before a contact window.

Validates:

```
TTL enforcement
retention cleanup
```

---

# 8. Developer Workflow

AetherNet emphasizes reproducibility and automated validation.

Primary developer commands:

```
make setup-dev
make test
make demo
make compare
```

Direct script usage:

```
scripts/run_demo.sh
scripts/run_compare.sh
```

The repository includes **50+ automated tests** verifying:

* queue ordering
* TTL expiration
* routing policy
* store persistence
* scenario execution
* documentation contracts

Continuous integration ensures all changes maintain **deterministic simulation behavior**.

---

# 9. Phase-1 Achievements

Phase-1 establishes a **fully functional DTN simulation framework**.

Capabilities implemented:

✓ deterministic event-driven simulator
✓ contact-aware routing
✓ strict priority scheduling
✓ store-carry-forward architecture
✓ bundle lifecycle tracking
✓ scenario-based experiments
✓ artifact export pipeline
✓ CI-validated repository
✓ architecture documentation

The platform is now suitable for **research experimentation and architecture exploration**.

---

# 10. Limitations

Phase-1 intentionally excludes several real-world complexities.

Not yet implemented:

* realistic network latency
* bandwidth constraints
* congestion control
* multi-path routing
* bundle fragmentation
* distributed node execution
* cryptographic bundle security

These limitations will be addressed in subsequent phases.

---

# 11. Phase-2 Roadmap

Phase-2 aims to introduce **transport realism**.

Planned additions:

### Bundle Protocol

Formal bundle schema including:

* source
* destination
* TTL
* payload
* creation time

---

### Link Model

Introduce realistic link properties:

* latency
* bandwidth
* capacity per contact window

---

### Congestion Control

Queue management strategies:

* drop lowest priority
* drop oldest bundles
* backpressure mechanisms

---

### Routing Tables

Support multi-hop routing beyond fixed paths.

Example topology:

```
Moon → Relay A → Relay B → Earth
```

---

### Node Abstraction

Introduce node runtime objects responsible for:

* queue management
* bundle storage
* forwarding logic

---

# 12. Phase-3 Vision

Phase-3 transforms AetherNet from a simulator into a **distributed experimental network**.

Potential capabilities:

* node daemons running independently
* network transport via gRPC or QUIC
* container deployment using Docker/Kubernetes
* constellation-scale simulation
* observability via Prometheus/Grafana

This stage would enable AetherNet to function as a **space networking research platform**.

---

# 13. Conclusion

AetherNet Phase-1 demonstrates the feasibility of building a **deterministic, modular DTN simulation platform** for exploring space network architectures.

By modeling contact-aware routing, strict priority scheduling, and store-carry-forward communication, the system captures essential behaviors of delay-tolerant space networks.

Future phases will introduce transport realism and distributed execution, progressively evolving AetherNet into a comprehensive **space networking research framework**.

---

# Phase-1 Final Status

```
Phase-1: COMPLETE
Test suite: PASSING
CI pipeline: PASSING
Architecture: STABLE
```

Next development stage:

```
Phase-2: Transport and Control Plane Realism
```

---

這份 whitepaper 建議你：

```
docs/whitepaper.md
```

提交到 repo。

然後在 README 加一行：

```
See the full architecture description in docs/whitepaper.md
```

---

