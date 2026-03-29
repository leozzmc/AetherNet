# AetherNet System Sequence — Phase Demo

## Purpose

This document describes how demo execution differs from base simulation.

Focus:

- routing-mode injection
- scenario-driven divergence
- deterministic comparison

---

## High-Level Flow

```text
Demo CLI
↓
Scenario Selection
↓
Routing Mode Injection
↓
Simulator Execution
↓
Routing Decision
↓
Forwarding Outcome
↓
Metrics Collection
↓
Artifact Export
```

````

---

## Detailed Sequence

```mermaid
sequenceDiagram
    participant CLI
    participant Scenario
    participant Simulator
    participant RoutingPolicy
    participant Store
    participant Metrics

    CLI->>Scenario: select scenario
    CLI->>Simulator: set routing_mode

    Scenario->>Simulator: initialize environment

    loop simulation ticks
        Simulator->>RoutingPolicy: evaluate decision
        RoutingPolicy-->>Simulator: next hop / hold

        alt forward
            Simulator->>Store: dequeue bundle
            Simulator->>NextHop: send bundle
            NextHop->>Metrics: record success
        else hold
            Simulator->>Store: keep bundle
        end
    end

    Simulator->>Metrics: finalize report
    Metrics->>CLI: output JSON / CSV
```

---

## Key Differences from Base Sequence

| Aspect          | Base       | Demo                  |
| --------------- | ---------- | --------------------- |
| routing control | internal   | CLI-controlled        |
| comparison      | implicit   | explicit              |
| output          | metrics    | artifact + comparison |
| purpose         | simulation | evaluation            |

---

## Design Principle

Demo layer enforces:

- identical scenario
- identical inputs
- only routing policy differs

---

## Result

This guarantees:

- fair comparison
- deterministic outcomes
- reproducible experiments

````
