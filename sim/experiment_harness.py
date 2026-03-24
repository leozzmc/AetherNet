from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from sim.scenarios import get_scenario
from sim.simulator import create_default_simulator


@dataclass(frozen=True)
class ExperimentCase:
    """
    Deterministic description of one experiment run.
    """

    case_name: str
    scenario_name: str
    tick_size: int = 1
    simulation_end_override: Optional[int] = None
    routing_mode: Optional[str] = None


@dataclass(frozen=True)
class ExperimentResult:
    """
    Deterministic summary of one completed experiment run.
    """

    case_name: str
    scenario_name: str
    final_metrics: Dict[str, Any]
    delivered_bundle_ids: List[str]
    store_bundle_ids_remaining: List[str]
    delivery_ratio: float
    unique_delivered: int
    duplicate_deliveries: int
    bundles_dropped_total: Any
    routing_mode: str = "baseline"


class ExperimentHarness:
    """
    Deterministic, sequential experiment runner.
    """

    @staticmethod
    def run_experiments(cases: List[ExperimentCase]) -> List[ExperimentResult]:
        results: List[ExperimentResult] = []

        for case in cases:
            try:
                profile = get_scenario(case.scenario_name)
            except ValueError as exc:
                raise ValueError(f"ExperimentCase '{case.case_name}' failed: {exc}") from exc

            resolved_routing_mode = case.routing_mode or profile.routing_mode

            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
                json.dump(profile.generate_plan(), plan_file)
                plan_path = Path(plan_file.name)

            try:
                with tempfile.TemporaryDirectory() as tmpstore:
                    simulator, _ = create_default_simulator(
                        plan_path=str(plan_path),
                        store_dir=tmpstore,
                        scenario_name=profile.name,
                        inject_short_lived=profile.inject_short_lived_bundle,
                        tick_size=case.tick_size,
                        simulation_end_override=case.simulation_end_override,
                        routing_mode=resolved_routing_mode,
                    )

                    report = simulator.run()
                    final_metrics = report.get("final_metrics", {})

                    results.append(
                        ExperimentResult(
                            case_name=case.case_name,
                            scenario_name=case.scenario_name,
                            final_metrics=final_metrics,
                            delivered_bundle_ids=list(report.get("delivered_bundle_ids", [])),
                            store_bundle_ids_remaining=list(report.get("store_bundle_ids_remaining", [])),
                            delivery_ratio=float(final_metrics.get("delivery_ratio", 0.0)),
                            unique_delivered=int(final_metrics.get("unique_delivered", 0)),
                            duplicate_deliveries=int(final_metrics.get("duplicate_deliveries", 0)),
                            bundles_dropped_total=final_metrics.get("bundles_dropped_total", {}),
                            routing_mode=report.get("routing_mode", resolved_routing_mode),
                        )
                    )
            finally:
                if plan_path.exists():
                    plan_path.unlink()

        return results

    @staticmethod
    def generate_summary(results: List[ExperimentResult]) -> Dict[str, Any]:
        """
        Produce a stable, comparison-friendly summary while preserving result order.
        """
        return {
            "total_cases": len(results),
            "cases": [
                {
                    "case_name": result.case_name,
                    "scenario_name": result.scenario_name,
                    "routing_mode": result.routing_mode,
                    "delivery_ratio": result.delivery_ratio,
                    "unique_delivered": result.unique_delivered,
                    "duplicate_deliveries": result.duplicate_deliveries,
                    "bundles_dropped_total": result.bundles_dropped_total,
                    "store_remaining": len(result.store_bundle_ids_remaining),
                }
                for result in results
            ],
        }
