import json
from pathlib import Path
from typing import Dict, Any, List


def summarize_report(report: Dict[str, Any], initial_injected_count: int = 0) -> Dict[str, Any]:
    """Extract a stable compact summary with derived metrics from a single scenario report."""
    metrics = report.get("final_metrics", {})

    forwarded_total = sum(metrics.get("bundles_forwarded_total", {}).values())
    stored_total = sum(metrics.get("bundles_stored_total", {}).values())
    delivered_total = sum(metrics.get("bundles_delivered_total", {}).values())
    expired_total = sum(metrics.get("bundles_expired_total", {}).values())

    remaining_store_count = len(report.get("store_bundle_ids_remaining", []))
    purged_count = len(report.get("purged_bundle_ids", []))
    delivered_bundle_count = len(report.get("delivered_bundle_ids", []))

    base_count = report.get("injected_bundle_count", initial_injected_count)
    if base_count < 0:
        base_count = 0

    delivered_ratio = round(delivered_bundle_count / base_count, 2) if base_count else 0.0
    expired_ratio = round(expired_total / base_count, 2) if base_count else 0.0
    purged_ratio = round(purged_count / base_count, 2) if base_count else 0.0
    remaining_store_ratio = round(remaining_store_count / base_count, 2) if base_count else 0.0

    if expired_total > 0 or purged_count > 0:
        outcome = "expiry_observed"
    elif delivered_bundle_count == 0:
        outcome = "no_delivery"
    elif base_count > 0 and delivered_bundle_count < base_count:
        outcome = "partial_delivery"
    else:
        outcome = "successful_delivery"

    return {
        "scenario_name": report.get("scenario_name", "unknown"),
        "simulation_end_time": report.get("simulation_end_time", 0),
        "outcome": outcome,
        "forwarded_total": forwarded_total,
        "stored_total": stored_total,
        "delivered_total": delivered_total,
        "expired_total": expired_total,
        "remaining_store_count": remaining_store_count,
        "purged_count": purged_count,
        "delivered_bundle_count": delivered_bundle_count,
        "delivered_ratio": delivered_ratio,
        "expired_ratio": expired_ratio,
        "purged_ratio": purged_ratio,
        "remaining_store_ratio": remaining_store_ratio,
    }


def compare_reports(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple scenario reports into an enriched comparison summary."""
    summaries = [summarize_report(r) for r in reports]

    total_delivered_bundles = sum(s["delivered_bundle_count"] for s in summaries)
    total_expired_bundles = sum(s["expired_total"] for s in summaries)
    total_purged_bundles = sum(s["purged_count"] for s in summaries)

    successful_scenarios = [s["scenario_name"] for s in summaries if s["outcome"] == "successful_delivery"]
    scenarios_with_expiry = [s["scenario_name"] for s in summaries if s["outcome"] == "expiry_observed"]

    max_remaining = max((s["remaining_store_count"] for s in summaries), default=0)
    max_delivered = max((s["delivered_bundle_count"] for s in summaries), default=0)

    return {
        "scenario_names": [s["scenario_name"] for s in summaries],
        "per_scenario_summaries": summaries,
        "aggregate": {
            "total_delivered_bundles": total_delivered_bundles,
            "total_expired_bundles": total_expired_bundles,
            "total_purged_bundles": total_purged_bundles,
            "successful_scenarios": successful_scenarios,
            "scenarios_with_expiry": scenarios_with_expiry,
            "max_remaining_store_count": max_remaining,
            "max_delivered_bundle_count": max_delivered,
        },
    }


def write_json_report(data: Dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    return output_path