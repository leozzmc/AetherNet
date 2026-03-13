# ADR 0009: Lightweight Lifecycle Timelines

**Date**: 2026-03-13
**Status**: Accepted

## Context
To prove that AetherNet behaves correctly under extreme delays (e.g., relay buffering, queue wait times), we need to track when a bundle is stored vs. delivered. However, integrating a full observability stack (Prometheus histograms, OpenTelemetry spans) into a Python MVP adds immense overhead and distracts from core DTN mechanisms.

## Decision
We implemented a lightweight `bundle_timelines` dictionary inside the Simulator. It records the exact simulation tick (integer) of key state transitions (`forwarded_tick`, `stored_tick`, `delivered_tick`, `purged_tick`) per bundle.

## Rationale
1. **Demo Storytelling**: By deriving `first_delivery_tick` and `relay_storage_observed` directly from the report JSON, researchers can instantly compare scenarios (e.g., proving `delayed_delivery` took 30 ticks longer than `default`).
2. **Honest Abstraction**: We explicitly document these as "Simulation Ticks" rather than real-world latency (ms), keeping expectations realistic for an Application-Layer simulator.
3. **No External Dependencies**: This keeps the codebase standard-library only, maintaining execution speed and test simplicity.