# AetherNet

**A Secure Delay-Tolerant Distributed Infrastructure Prototype for Space Networks**

## Project Purpose
AetherNet explores how to build a secure, contact-aware, delay-tolerant message infrastructure for space-like environments with intermittent connectivity and long delays.

### AetherNet vs LunarNet
- **AetherNet**: The core platform and simulation architecture.
- **LunarNet**: The reference deployment scenario using an `Earth ↔ LEO ↔ Moon` topology.

## MVP Scope (through Wave 8)
This repository provides a highly repeatable, application-layer DTN experimental platform with:
- ✅ **Contact-Aware Forwarding**: Bundles move only during valid orbital windows.
- ✅ **Store-Carry-Forward**: Filesystem-backed DTN store prevents data loss during link outages.
- ✅ **Strict Priority Delivery**: Telemetry is forwarded ahead of Science data.
- ✅ **Data Retention & Expiry**: Expired bundles are skipped during forwarding and periodically purged from the DTN store.
- ✅ **Experimental Scenarios**: Built-in profiles (e.g., delayed delivery, expiry before contact).
- ✅ **End-of-Run Reporting & Analytics**: Machine-readable JSON reports, multi-scenario comparisons, and derived metrics (e.g., delivery ratios, outcome classifications).

## Current Non-Goals
Intentionally out of scope for the MVP:
- Real network transport (HTTP, gRPC, TCP/UDP data plane)
- Distributed task scheduling / Kubernetes (K3s)
- Orbital mechanics or RF-layer simulation
- Database-backed persistence

## Running Experiments

**Run a single scenario and export the report:**
```bash
./scripts/run_demo.sh --scenario delayed_delivery --report-out artifacts/reports/delayed_delivery.json
```

Run all built-in scenarios and generate an aggregate comparison:

```
./scripts/run_compare.sh
```
Outputs will be securely written to the `artifacts/` directory. See `docs/artifacts.md` for details.

##  Testing

Run the test suite from the repository root:

```bash
export PYTHONPATH=$(pwd)
pytest tests/
```



---

System Topology

```mermaid
graph TD

subgraph Earth_Segment
    EC[Earth Cloud / Control Plane]
    GS[Ground Station Gateway]
end

subgraph LEO_Constellation
    LEO1[LEO Satellite A<br>Edge Compute]
    LEO2[LEO Satellite B<br>Relay Storage]
end

subgraph Lunar_Segment
    LR[Lunar Relay Orbiter]
    MB[Moon Base Node]
    MR[Moon Rover]
end

EC -->|Internet| GS
GS -->|Uplink Downlink<br>30-80 ms| LEO1
LEO1 -->|Inter Satellite Link<br>10-30 ms| LEO2
LEO2 -->|Deep Space Link<br>1-2 s| LR
LR -->|Orbital Relay| MB
MB -->|Surface Network| MR
```

AetherNet Node Architecture

```mermaid
graph TD

subgraph AetherNet_Node
    direction TB

    subgraph Security_Layer
        SPIRE[SPIRE Agent<br>Node Identity]
        MTLS[mTLS Secure Communication]
    end

    subgraph Compute_Storage_Layer
        Scheduler[Distributed Task Scheduler]
        DTNStore[DTN Object Storage<br>Store Carry Forward]
    end

    subgraph Infrastructure_Layer
        K3S[K3s Container Runtime]
        NetSim[Network Simulation<br>tc / toxiproxy]
    end

end

Users[Users / Applications]
Control[Earth Control Plane]

Users --> Scheduler
Scheduler --> DTNStore

Control --> SPIRE
SPIRE --> MTLS

Scheduler --> MTLS
DTNStore --> MTLS

MTLS --> K3S
K3S --> NetSim

NodeA[Space Node A]
NodeB[Space Node B]

NodeA -->|Secure DTN Transfer| NodeB
```

Data Flow

```mermaid
sequenceDiagram
    participant Rover
    participant LunarNode
    participant Relay
    participant Ground

    Rover->>LunarNode: Telemetry Data
    LunarNode->>Relay: Store Bundle
    Relay-->>Relay: Cache (Link unavailable)
    Relay->>Ground: Forward when link opens
    Ground->>Ground: Process Data
```
