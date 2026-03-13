import json
from pathlib import Path
from typing import Dict, Any, List


def summarize_report(report: Dict[str, Any], initial_injected_count: int = 0) -> Dict[str, Any]:
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
    remaining_ratio = round(remaining_store_count / base_count, 2) if base_count else 0.0

    if expired_total > 0 or purged_count > 0:
        outcome = "expiry_observed"
    elif delivered_bundle_count == 0:
        outcome = "no_delivery"
    elif base_count > 0 and delivered_bundle_count < base_count:
        outcome = "partial_delivery"
    else:
        outcome = "successful_delivery"

    timelines = report.get("bundle_timelines", {})
    delivered_ticks = [t.get("delivered_tick") for t in timelines.values() if "delivered_tick" in t]
    purged_ticks = [t.get("purged_tick") for t in timelines.values() if "purged_tick" in t]
    stored_ticks = [t.get("stored_tick") for t in timelines.values() if "stored_tick" in t]

    first_delivery = min(delivered_ticks) if delivered_ticks else None
    last_delivery = max(delivered_ticks) if delivered_ticks else None
    avg_delivery = round(sum(delivered_ticks) / len(delivered_ticks), 1) if delivered_ticks else None
    delivery_span = (
        last_delivery - first_delivery
        if first_delivery is not None and last_delivery is not None
        else None
    )
    first_purge = min(purged_ticks) if purged_ticks else None
    relay_storage_observed = len(stored_ticks) > 0

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
        "remaining_store_ratio": remaining_ratio,
        "first_delivery_tick": first_delivery,
        "last_delivery_tick": last_delivery,
        "average_delivery_tick": avg_delivery,
        "first_purge_tick": first_purge,
        "delivery_span_ticks": delivery_span,
        "relay_storage_observed": relay_storage_observed,
    }


def compare_reports(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    summaries = [summarize_report(r) for r in reports]

    total_delivered_bundles = sum(s["delivered_bundle_count"] for s in summaries)
    total_expired_bundles = sum(s["expired_total"] for s in summaries)
    total_purged_bundles = sum(s["purged_count"] for s in summaries)

    successful_scenarios = [s["scenario_name"] for s in summaries if s["outcome"] == "successful_delivery"]
    scenarios_with_expiry = [s["scenario_name"] for s in summaries if s["outcome"] == "expiry_observed"]

    max_remaining = max((s["remaining_store_count"] for s in summaries), default=0)
    max_delivered = max((s["delivered_bundle_count"] for s in summaries), default=0)

    valid_first_ticks = [s["first_delivery_tick"] for s in summaries if s["first_delivery_tick"] is not None]
    valid_last_ticks = [s["last_delivery_tick"] for s in summaries if s["last_delivery_tick"] is not None]

    fastest_delivery_tick = min(valid_first_ticks) if valid_first_ticks else None
    slowest_delivery_tick = max(valid_last_ticks) if valid_last_ticks else None
    scenarios_with_relay_storage = [s["scenario_name"] for s in summaries if s.get("relay_storage_observed")]
    scenarios_with_purge_events = [s["scenario_name"] for s in summaries if s.get("first_purge_tick") is not None]

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
            "fastest_delivery_tick": fastest_delivery_tick,
            "slowest_delivery_tick": slowest_delivery_tick,
            "scenarios_with_relay_storage": scenarios_with_relay_storage,
            "scenarios_with_purge_events": scenarios_with_purge_events,
        },
    }


def write_json_report(data: Dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    return output_path