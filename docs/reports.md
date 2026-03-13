# Interpreting AetherNet Reports

AetherNet generates machine-readable JSON reports to help validate and compare the behavior of different DTN scenarios.

## Individual Reports & Derived Summaries
A full report contains the complete `final_metrics` snapshot and detailed bundle IDs. For higher-level interpretation, AetherNet generates a **Derived Summary** containing:
- `forwarded_total`: Total forwarding events across all hops.
- `delivered_bundle_count`: Absolute number of unique bundles successfully reaching the ground station.
- `delivered_ratio`: The percentage of initially injected bundles that were successfully delivered (0.0 to 1.0).
- `outcome`: A deterministic classification of the run (`successful_delivery`, `partial_delivery`, `expiry_observed`, `no_delivery`).

## Expected Outcomes for Built-in Scenarios

1. **`default_multihop`**
   - **Expected Outcome**: `successful_delivery`. `delivered_ratio` should be 1.0.
   - **Meaning**: The contact windows are sufficient to move data end-to-end securely.

2. **`delayed_delivery`**
   - **Expected Outcome**: `successful_delivery`. Identical delivery counts to the default, but observing the simulation logs will show bundles sitting in `STORED` status at the relay for a much longer period.
   - **Meaning**: Validates the Store-Carry-Forward mechanism during prolonged outages.

3. **`expiry_before_contact`**
   - **Expected Outcome**: `expiry_observed`. `purged_ratio` > 0.0. 
   - **Meaning**: Validates that the DTN Router respects TTL constraints and that the Retention job correctly garbage-collects stale data, saving valuable bandwidth and storage.