from __future__ import annotations

import argparse
import csv
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Sequence

from sim.experiment_harness import ExperimentCase, ExperimentHarness, ExperimentResult
from sim.scenarios import list_scenarios


SCHEMA_VERSION = "aethernet-demo-v1"
CURATED_DEMO_SCENARIOS = [
    "default_multihop",
    "delayed_delivery",
    "expiry_before_contact",
]
DEFAULT_OUTPUT_DIR = Path("artifacts/demo")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run AetherNet's deterministic, scenario-driven demo using the "
            "existing ExperimentHarness API."
        )
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help=(
            "Run one or more specific scenarios. May be repeated, e.g. "
            "--scenario default_multihop --scenario delayed_delivery"
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all registered scenarios instead of the curated demo set.",
    )
    parser.add_argument(
        "--tick-size",
        type=int,
        default=1,
        help="Tick size forwarded into ExperimentCase (default: 1).",
    )
    parser.add_argument(
        "--simulation-end",
        type=int,
        default=None,
        help="Optional simulation end override passed into ExperimentCase.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for demo artifacts (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print traceback for unexpected failures.",
    )
    return parser.parse_args(argv)


def _validate_args(args: argparse.Namespace) -> None:
    if args.tick_size <= 0:
        raise ValueError("--tick-size must be a positive integer")
    if args.simulation_end is not None and args.simulation_end <= 0:
        raise ValueError("--simulation-end must be a positive integer when provided")


def _resolve_scenarios(args: argparse.Namespace) -> List[str]:
    available = list_scenarios()
    available_set = set(available)

    if args.all:
        return available

    requested = args.scenario or CURATED_DEMO_SCENARIOS
    unknown = [scenario for scenario in requested if scenario not in available_set]
    if unknown:
        raise ValueError(
            f"Unknown scenario(s): {unknown}. Available scenarios: {available}"
        )
    return requested


def _build_cases(
    scenario_names: Sequence[str],
    tick_size: int,
    simulation_end_override: int | None,
) -> List[ExperimentCase]:
    return [
        ExperimentCase(
            case_name=f"demo::{scenario_name}",
            scenario_name=scenario_name,
            tick_size=tick_size,
            simulation_end_override=simulation_end_override,
        )
        for scenario_name in scenario_names
    ]


def _serialize_dropped_total(value: Any) -> Any:
    if isinstance(value, dict):
        return dict(sorted(value.items()))
    return value


def _result_to_row(result: ExperimentResult) -> Dict[str, Any]:
    return {
        "case_name": result.case_name,
        "scenario_name": result.scenario_name,
        "delivery_ratio": result.delivery_ratio,
        "unique_delivered": result.unique_delivered,
        "duplicate_deliveries": result.duplicate_deliveries,
        "store_remaining_count": len(result.store_bundle_ids_remaining),
        "store_bundle_ids_remaining": result.store_bundle_ids_remaining,
        "delivered_bundle_ids": result.delivered_bundle_ids,
        "bundles_dropped_total": _serialize_dropped_total(result.bundles_dropped_total),
    }


def _write_json(path: Path, data: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_name",
        "scenario_name",
        "delivery_ratio",
        "unique_delivered",
        "duplicate_deliveries",
        "store_remaining_count",
        "store_bundle_ids_remaining",
        "delivered_bundle_ids",
        "bundles_dropped_total",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            serialized["store_bundle_ids_remaining"] = json.dumps(
                serialized["store_bundle_ids_remaining"]
            )
            serialized["delivered_bundle_ids"] = json.dumps(
                serialized["delivered_bundle_ids"]
            )
            serialized["bundles_dropped_total"] = json.dumps(
                serialized["bundles_dropped_total"]
            )
            writer.writerow(serialized)

    return path


def _print_summary(results: Sequence[ExperimentResult]) -> None:
    print("=== AetherNet Demo Results ===")
    print()
    for result in results:
        print(f"[{result.scenario_name}]")
        print(f"  delivery_ratio      : {result.delivery_ratio:.3f}")
        print(f"  unique_delivered    : {result.unique_delivered}")
        print(f"  duplicate_deliveries: {result.duplicate_deliveries}")
        print(
            "  store_remaining_count: "
            f"{len(result.store_bundle_ids_remaining)}"
        )
        print(f"  bundles_dropped_total: {result.bundles_dropped_total}")
        print()

    if results:
        best = max(results, key=lambda result: result.delivery_ratio)
        worst = min(results, key=lambda result: result.delivery_ratio)
        print("=== Demo Conclusion ===")
        print(f"Best scenario : {best.scenario_name} ({best.delivery_ratio:.3f})")
        print(f"Worst scenario: {worst.scenario_name} ({worst.delivery_ratio:.3f})")


def run_demo(
    scenario_names: Sequence[str],
    tick_size: int = 1,
    simulation_end_override: int | None = None,
) -> List[ExperimentResult]:
    cases = _build_cases(
        scenario_names=scenario_names,
        tick_size=tick_size,
        simulation_end_override=simulation_end_override,
    )
    return ExperimentHarness.run_experiments(cases)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        _validate_args(args)
        scenario_names = _resolve_scenarios(args)
        results = run_demo(
            scenario_names=scenario_names,
            tick_size=args.tick_size,
            simulation_end_override=args.simulation_end,
        )
        summary = ExperimentHarness.generate_summary(results)
        rows = [_result_to_row(result) for result in results]

        output_dir = args.output_dir
        json_path = output_dir / "demo.json"
        csv_path = output_dir / "demo.csv"

        json_payload = {
            "schema_version": SCHEMA_VERSION,
            "summary": summary,
            "results": rows,
        }

        _write_json(json_path, json_payload)
        _write_csv(csv_path, rows)
        _print_summary(results)

        print()
        print(f"JSON summary written to: {json_path}")
        print(f"CSV summary written to : {csv_path}")
        return 0
    except Exception as exc:
        print(f"[demo.py] ERROR: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
