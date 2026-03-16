from typing import Any, Dict


def build_visualization_spec(comparison: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wave-35: Deterministic research-visualization preparation layer.
    
    Transforms the output of compare_reports(...) into a stable, machine-readable 
    visualization spec dictionary. This payload can be consumed by external 
    plotting libraries, notebooks, or dashboards without tying the simulator 
    to specific rendering frameworks.
    """
    if not isinstance(comparison, dict):
        raise ValueError("Input comparison must be a dictionary.")

    if "per_scenario_summaries" not in comparison:
        raise ValueError("Input must contain 'per_scenario_summaries'.")

    summaries = comparison["per_scenario_summaries"]
    if not isinstance(summaries, list):
        raise ValueError("'per_scenario_summaries' must be a list.")

    scenario_names = []
    delivered_bundles = []
    expired_bundles = []
    remaining_stores = []
    delivered_fragments = []
    expired_fragments = []
    outcomes = []

    # Preserve order deterministically based on the input list
    for summary in summaries:
        if "scenario_name" not in summary:
            raise ValueError("Scenario summary missing 'scenario_name'.")

        name = summary["scenario_name"]
        scenario_names.append(name)
        delivered_bundles.append(summary.get("delivered_bundle_count", 0))
        expired_bundles.append(summary.get("expired_total", 0))
        remaining_stores.append(summary.get("remaining_store_count", 0))
        delivered_fragments.append(summary.get("fragments_delivered_total", 0))
        expired_fragments.append(summary.get("fragments_expired_total", 0))

        outcomes.append({
            "scenario_name": name,
            "outcome": summary.get("outcome", "unknown")
        })

    return {
        "meta": {
            "scenario_count": len(scenario_names),
            "source_type": "comparison_report"
        },
        "charts": {
            "delivery_by_scenario": {
                "type": "bar",
                "x": scenario_names,
                "y": delivered_bundles,
            },
            "expiry_by_scenario": {
                "type": "bar",
                "x": scenario_names,
                "y": expired_bundles,
            },
            "remaining_store_by_scenario": {
                "type": "bar",
                "x": scenario_names,
                "y": remaining_stores,
            },
            "fragment_delivery_by_scenario": {
                "type": "bar",
                "x": scenario_names,
                "y": delivered_fragments,
            },
            "fragment_expiry_by_scenario": {
                "type": "bar",
                "x": scenario_names,
                "y": expired_fragments,
            },
            "outcome_by_scenario": {
                "type": "categorical",
                "items": outcomes,
            }
        }
    }


def build_visualization_spec_from_experiment_batch(batch_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to extract the aggregate comparison from a Wave-34 experiment batch 
    and build a visualization spec.
    """
    if not isinstance(batch_result, dict):
        raise ValueError("Input batch_result must be a dictionary.")
        
    if "aggregate_comparison" not in batch_result:
        raise ValueError("Input must contain 'aggregate_comparison' from an experiment batch.")
        
    return build_visualization_spec(batch_result["aggregate_comparison"])