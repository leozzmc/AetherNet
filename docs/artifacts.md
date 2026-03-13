# AetherNet Artifacts

Simulation outputs are written under:

```
artifacts/
```

Directory layout:

```
artifacts/
reports/
default_multihop.json
delayed_delivery.json
expiry_before_contact.json
comparison/
    scenario_comparison.json
```

---

## Report Structure

Each scenario report contains:

### bundle_timelines

Lifecycle timestamps for each bundle.

Example:

```

"tel-001": {
"stored_tick": 5,
"first_forwarded_tick": 5,
"delivered_tick": 15
}

```

---

### forwarding metrics

```

bundles_forwarded_total
bundles_delivered_total
bundles_expired_total

```

These metrics describe the behavior of the forwarding layer.

---

### queue depths

```

queue_depth_lunar
queue_depth_relay

```

Snapshots of queue states at the end of the simulation.

---

### purged bundles

Expired bundles appear under:

```

purged_bundle_ids
recent_purged_ids

```

Example:

```

"purged_bundle_ids": ["tel-short"]

```

---

## Interpreting Results

Typical patterns:

| Scenario | Expected outcome |
|--------|--------|
| default_multihop | bundles delivered normally |
| delayed_delivery | delivery delayed due to contact plan |
| expiry_before_contact | bundle expiration occurs |

