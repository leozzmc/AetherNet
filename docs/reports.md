# Interpreting AetherNet Reports

AetherNet generates machine-readable JSON reports to help validate and compare the behavior of different DTN scenarios.

## Individual Reports & Derived Summaries
A full report contains the complete metrics snapshot, detailed bundle IDs, and a **Lightweight Lifecycle Timeline** (`bundle_timelines`) mapping event ticks per bundle.

For higher-level interpretation, AetherNet generates a **Derived Summary** containing:
- `forwarded_total`: Total forwarding events across all hops.
- `delivered_ratio`: The percentage of initially injected bundles successfully delivered (0.0 to 1.0).
- `outcome`: A deterministic classification (`successful_delivery`, `expiry_observed`, etc.).

### Timing-style Derived Metrics
These metrics provide behavioral insights based on simulation ticks (not real network latency in ms/ns):
- `first_delivery_tick`: The tick when the very first bundle arrived at the destination.
- `last_delivery_tick`: The tick when the final bundle arrived.
- `delivery_span_ticks`: `last_delivery_tick` - `first_delivery_tick`. Highlights how spread out the reception was.
- `relay_storage_observed`: Boolean. If true, bundles successfully waited in the intermediate relay node's DTN Store before moving on.

## Expected Outcomes for Built-in Scenarios

1. **`default_multihop`**
   - **Expected**: `successful_delivery`. `relay_storage_observed` should be True.
   - **Meaning**: Contact windows are sufficient. Bundles use the relay as a stepping stone.

2. **`delayed_delivery`**
   - **Expected**: `successful_delivery`. The `average_delivery_tick` will be significantly higher than the default scenario.
   - **Meaning**: Validates the Store-Carry-Forward mechanism effectively holds data securely over a prolonged connection gap.

3. **`expiry_before_contact`**
   - **Expected**: `expiry_observed`. `first_purge_tick` will be populated.
   - **Meaning**: Validates that Retention correctly drops stale data before wasting contact window bandwidth.