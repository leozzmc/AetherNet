# AetherNet System Sequence (Wave-58)

## Purpose

Describe the **full system lifecycle** across:

- simulation
- experiment execution
- research output

---

# 1. Runtime Lifecycle (DTN Core)

```mermaid
sequenceDiagram
    participant Source
    participant Router
    participant Store
    participant Relay
    participant Ground

    Source->>Router: Generate Bundle
    Router->>Store: Store (no contact)
    Store-->>Store: Hold

    Note over Router,Relay: Contact Opens

    Router->>Relay: Forward
    Relay->>Store: Store

    Note over Relay,Ground: Contact Opens

    Relay->>Ground: Forward
    Ground->>Ground: Deliver
```

---

# 2. Experiment Lifecycle

```mermaid
sequenceDiagram
    participant Scenario
    participant Harness
    participant Runner
    participant Metrics
    participant Export

    Scenario->>Harness: Load Scenario
    Harness->>Runner: Execute
    Runner->>Metrics: Emit Metrics
    Metrics->>Export: Serialize CSV
```

---

# 3. Research Lifecycle

```mermaid
sequenceDiagram
    participant Export
    participant Artifact
    participant Catalog
    participant Compare
    participant Table

    Export->>Artifact: Create Bundle
    Artifact->>Catalog: Register
    Catalog->>Compare: Load Batches
    Compare->>Table: Generate CSV
```

---

# 4. Unified Lifecycle

```text
Bundle Flow
→ Simulation
→ Experiment Execution
→ Metrics
→ Artifact
→ Catalog
→ Comparison
→ Paper Output
```

---

# AetherNet

A Secure Delay-Tolerant Distributed Infrastructure Prototype for Space Networks

---

## System Overview

AetherNet is a DTN-inspired system designed for:

- intermittent connectivity
- high latency
- space-like environments

---

## Current Capability (Wave-58)

### Core

- contact-aware routing
- store-carry-forward
- priority scheduling

### Experiment

- deterministic harness
- matrix execution

### Research

- artifact bundles
- catalog system
- batch comparison
- paper-ready export

---

## System Pipeline

```text
Simulation → Experiment → Artifact → Catalog → Comparison → Paper Output
```

---
