from __future__ import annotations

import argparse
import csv
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List

from sim.experiment_harness import ExperimentCase, ExperimentHarness, ExperimentResult
from sim.scenarios import list_scenarios

SCHEMA_VERSION = "aethernet-demo-v1"
CURATED_DEMO_SCENARIOS = [
    "default_multihop",
    "delayed_delivery",
    "expiry_before_contact",
    "multipath_competition",
    "contact_timing_tradeoff",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AetherNet scenario demo runner")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--tick-size", type=int, default=1)
    parser.add_argument("--simulation-end", type=int, default=None)
    parser.add_argument("--routing-mode", choices=["baseline", "contact_aware", "multipath"])
    parser.add_argument("--output-dir", default="artifacts/demo")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def _resolve_scenarios(args: argparse.Namespace) -> List[str]:
    available = set(list_scenarios())
    if args.all:
        return list_scenarios()
    if args.scenario:
        for name in args.scenario:
            if name not in available:
                raise ValueError(f"Unknown scenario: {name} | available={sorted(available)}")
        return args.scenario
    return CURATED_DEMO_SCENARIOS


def _build_cases(
    scenarios: List[str],
    tick_size: int,
    simulation_end: int | None,
    routing_mode: str | None,
) -> List[ExperimentCase]:
    return [
        ExperimentCase(
            case_name=f"demo::{scenario}",
            scenario_name=scenario,
            tick_size=tick_size,
            simulation_end_override=simulation_end,
            routing_mode=routing_mode,
        )
        for scenario in scenarios
    ]


def _result_to_row(result: ExperimentResult) -> Dict[str, Any]:
    return {
        "case_name": result.case_name,
        "scenario_name": result.scenario_name,
        "routing_mode": result.routing_mode,
        "delivery_ratio": result.delivery_ratio,
        "unique_delivered": result.unique_delivered,
        "duplicate_deliveries": result.duplicate_deliveries,
        "store_remaining_count": len(result.store_bundle_ids_remaining),
        "store_bundle_ids_remaining": result.store_bundle_ids_remaining,
        "delivered_bundle_ids": result.delivered_bundle_ids,
        "bundles_dropped_total": result.bundles_dropped_total,
    }


def _write_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _print_summary(results: List[ExperimentResult]) -> None:
    print("=== AetherNet Demo Results ===\n")
    for result in results:
        print(f"[{result.scenario_name}]")
        print(f"  routing_mode         : {result.routing_mode}")
        print(f"  delivery_ratio       : {result.delivery_ratio:.3f}")
        print(f"  unique_delivered     : {result.unique_delivered}")
        print(f"  duplicate_deliveries : {result.duplicate_deliveries}")
        print(f"  store_remaining_count: {len(result.store_bundle_ids_remaining)}")
        print(f"  bundles_dropped_total: {result.bundles_dropped_total}")
        print()

    best = max(results, key=lambda r: r.delivery_ratio)
    worst = min(results, key=lambda r: r.delivery_ratio)
    print("=== Demo Conclusion ===")
    print(f"Best scenario : {best.scenario_name} ({best.delivery_ratio:.3f})")
    print(f"Worst scenario: {worst.scenario_name} ({worst.delivery_ratio:.3f})")


def main() -> int:
    args = _parse_args()
    try:
        scenarios = _resolve_scenarios(args)
        cases = _build_cases(scenarios, args.tick_size, args.simulation_end, args.routing_mode)
        results = ExperimentHarness.run_experiments(cases)
        summary = ExperimentHarness.generate_summary(results)
        rows = [_result_to_row(result) for result in results]

        output_dir = Path(args.output_dir)
        json_data = {
            "schema_version": SCHEMA_VERSION,
            "summary": summary,
            "results": rows,
        }
        _write_json(json_data, output_dir / "demo.json")
        _write_csv(rows, output_dir / "demo.csv")
        _print_summary(results)
        print(f"\nJSON summary written to: {output_dir / 'demo.json'}")
        print(f"CSV summary written to : {output_dir / 'demo.csv'}")
        return 0
    except Exception as exc:
        print(f"[demo.py] ERROR: {exc}")
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
