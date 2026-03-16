from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sim.reporting import compare_reports, summarize_report
from sim.run_helpers import run_named_scenario


@dataclass(frozen=True)
class ExperimentSpec:
    """
    Wave-34: Defines the parameters for a single, deterministic simulation experiment.
    """
    name: str
    scenario_name: str
    tick_size: int = 1
    end_time_override: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Experiment name must not be empty.")
        if not self.scenario_name or not self.scenario_name.strip():
            raise ValueError("Scenario name must not be empty.")
        if self.tick_size <= 0:
            raise ValueError("tick_size must be strictly positive (> 0).")
        if self.end_time_override is not None and self.end_time_override <= 0:
            raise ValueError("end_time_override must be strictly positive (> 0).")


def run_experiment(spec: ExperimentSpec) -> Dict[str, Any]:
    """
    Execute a single experiment based on the provided specification.
    Returns a structured dictionary containing metadata, the raw report, and a summary.
    """
    raw_report = run_named_scenario(
        scenario_name=spec.scenario_name,
        tick_size=spec.tick_size,
        end_time_override=spec.end_time_override,
    )

    summary = summarize_report(raw_report)

    return {
        "experiment_name": spec.name,
        "scenario_name": spec.scenario_name,
        "tick_size": spec.tick_size,
        "end_time_override": spec.end_time_override,
        "report": raw_report,
        "summary": summary,
    }


def run_experiments(specs: List[ExperimentSpec]) -> Dict[str, Any]:
    """
    Execute a batch of experiments sequentially.
    Ensures experiment names are unique and produces an aggregate comparison.
    """
    seen_names = set()
    for spec in specs:
        if spec.name in seen_names:
            raise ValueError(f"Duplicate experiment name detected: '{spec.name}'")
        seen_names.add(spec.name)

    results = []
    raw_reports = []
    experiment_names = []

    for spec in specs:
        result = run_experiment(spec)
        results.append(result)
        raw_reports.append(result["report"])
        experiment_names.append(spec.name)

    aggregate_comparison = compare_reports(raw_reports)

    return {
        "experiment_names": experiment_names,
        "results": results,
        "aggregate_comparison": aggregate_comparison,
    }