# ADR 0004: Retention and Expiry Synchronization

**Date**: 2026-03-13
**Status**: Accepted

## Context
In a DTN, bundles have a Time-To-Live (TTL). When links are down for extended periods, bundles may expire. We need to ensure expired bundles do not consume disk space or queue memory, and are never forwarded.

## Decision
We integrate expiration checks at two distinct layers:
1. **Just-In-Time (JIT) Queue Purge**: The `StrictPriorityQueue` checks TTL at the exact moment of `dequeue()`. If expired, it drops the bundle and logs it.
2. **Periodic Store Garbage Collection**: The `Simulator` runs a background task (every 5 ticks) calling `purge_expired()` to clean up the filesystem store.

## Rationale & Tradeoffs
We intentionally **deferred perfect real-time synchronization** between the Queue (Memory) and the Store (Disk).
If a bundle expires while sitting in the queue, its metadata remains on disk until the next 5-tick GC cycle. 
This trade-off is acceptable for the MVP because:
1. It prevents the need to tightly couple the Queue and Store interfaces.
2. The JIT check during dequeue guarantees that an expired bundle will *never* be forwarded over the network, satisfying the primary correctness requirement.