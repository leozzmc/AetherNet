# AetherNet Demonstration Guide

This document explains how to run the built-in demo scenarios and how to interpret the generated results.

AetherNet is a **delay-tolerant networking prototype** designed to explore store-carry-forward behavior under intermittent contact windows.

The demo scenarios simulate a simplified topology:

Lunar Node → Relay Satellite → Ground Station

Bundles are injected at the lunar node and forwarded across contact windows.

---

## Running the demo

Generate all scenarios:

```bash
make compare
````

Artifacts will appear in:

```
artifacts/reports/
artifacts/comparison/
```

---

## Included Scenarios

### default_multihop

Normal multi-hop delivery.

Expected behavior:

* telemetry bundles delivered first
* science bundles delivered after telemetry
* delivery occurs during the relay → ground contact window

Example timeline:

```
tel-001 delivered at tick 15
tel-002 delivered at tick 16
sci-001 delivered at tick 17
```

---

### delayed_delivery

Identical injection pattern but the second contact window is delayed.

Expected behavior:

* bundles are stored longer at the relay
* delivery occurs significantly later

Example timeline:

```
tel-001 delivered at tick 45
tel-002 delivered at tick 46
sci-001 delivered at tick 47
```

---

### expiry_before_contact

Demonstrates bundle expiration.

A short-TTL telemetry bundle is injected.

Expected behavior:

* bundle expires before relay contact
* it is purged from the DTN store
* remaining bundles stay buffered at the relay

Example event:

```
tel-short purged at tick 10
```

---

## Metrics Overview

Each scenario produces metrics including:

* bundles_forwarded_total
* bundles_delivered_total
* bundles_expired_total
* bundle lifecycle timelines
* queue depth snapshots

---