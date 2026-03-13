# AetherNet Artifacts Contract

To ensure reproducibility and ease of integration with future dashboards or analysis tools, AetherNet adheres to a strict output convention for all simulation artifacts.

## Directory Layout
When running the batch comparison tool (`./scripts/run_compare.sh`), outputs are written to the `artifacts/` directory at the repository root:

```text
artifacts/
├── comparison.json           # Aggregate summary of all executed scenarios
└── reports/
    ├── default_multihop.json # Full detailed report for a specific scenario
    ├── delayed_delivery.json
    └── expiry_before_contact.json
```

## Report Schemas

**Per-Scenario Report** ( `reports/*.json` )
The output of a single simulation run. It contains the complete `final_metrics` snapshot, along with lists of `delivered_bundle_ids` and `purged_bundle_ids` for deep debugging.

**Aggregate Comparison** (`comparison.json`)
A high-level overview combining the results of all scenarios. It contains `per_scenario_summaries` (compact versions of the full reports) and an `aggregate` section detailing total bundles delivered, expired, and purged across the entire experiment suite.