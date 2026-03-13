# AetherNet Metrics Model

AetherNet currently uses a lightweight in-memory metrics collector to validate MVP behavior.

## Tracked Metrics

- `bundles_forwarded_total`  
  Counter by bundle type. Increments whenever a bundle begins a forwarding step.

- `bundles_stored_total`  
  Counter by bundle type. Increments when a bundle completes a non-final hop and is stored at the relay.

- `bundles_delivered_total`  
  Counter by bundle type. Increments when a bundle reaches its final destination.

- `bundles_expired_total`  
  Counter by bundle type. Increments when an expired bundle is purged from persisted metadata.

- `recent_purged_ids`  
  Lightweight list of recently purged expired bundle IDs retained in the final snapshot.

- `last_queue_depths`  
  Dictionary containing the latest observed queue depths, currently using keys:
  - `queue_depth_lunar`
  - `queue_depth_relay`

## How These Metrics Support MVP Goals

These metrics help validate:
- whether telemetry is being forwarded ahead of science data
- whether bundles are being stored at the relay before second-hop delivery
- whether expired data is eventually cleaned up
- whether queue depth grows or drains as contact windows change

## Current Limitations

- metrics are in-memory only
- there is no HTTP `/metrics` endpoint yet
- no latency histogram or delivery-timing metric is implemented yet
- queue/store synchronization remains an intentional MVP simplification