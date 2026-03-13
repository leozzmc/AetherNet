# AetherNet Experimental Scenarios

AetherNet uses "Scenario Profiles" to validate how the DTN behaves under different extreme space conditions. You can run these using the `--scenario` flag in the simulator CLI.

## Built-in Scenarios

### 1. `default_multihop` (Default)
- **Goal**: Validate the core Store-Carry-Forward and strict priority mechanics.
- **Topology**: `lunar-node -> leo-relay -> ground-station`
- **Expected Outcome**: Telemetry is delivered first, followed by Science data. All bundles successfully reach the ground station before the simulation ends.

### 2. `delayed_delivery`
- **Goal**: Validate the relay's ability to safely hold data during prolonged link outages.
- **Topology**: The `leo-relay -> ground-station` link opens significantly later than the first hop.
- **Expected Outcome**: Bundles will be marked as `STORED` at the relay for a long duration, increasing the `queue_depth_relay` metric, before eventually being forwarded.

### 3. `expiry_before_contact`
- **Goal**: Validate the system's Garbage Collection (Retention/Expiry) mechanism.
- **Topology**: The first contact window opens *after* a short-lived telemetry bundle's TTL has expired.
- **Expected Outcome**: The expired bundle will NOT be forwarded. It will be identified by the retention job, dropped from the queue, purged from the store, and recorded in the `bundles_expired_total` metric.