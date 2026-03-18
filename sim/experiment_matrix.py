from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sim.experiment_harness import ExperimentCase


@dataclass(frozen=True)
class ExperimentMatrix:
    """
    Wave-53: Narrow, deterministic declarative matrix for generating ExperimentCase objects.

    This wave intentionally supports only the dimensions that are already part of the
    current ExperimentCase contract:
    - scenario_names
    - tick_sizes
    - simulation_end_overrides
    """
    scenario_names: List[str]
    tick_sizes: List[int] = field(default_factory=lambda: [1])
    simulation_end_overrides: List[Optional[int]] = field(default_factory=lambda: [None])

    def __post_init__(self) -> None:
        if not self.scenario_names:
            raise ValueError("ExperimentMatrix must include at least one scenario name.")

        if not self.tick_sizes:
            raise ValueError("ExperimentMatrix must include at least one tick size.")

        if not self.simulation_end_overrides:
            raise ValueError("ExperimentMatrix must include at least one simulation end override.")

        for tick_size in self.tick_sizes:
            if tick_size <= 0:
                raise ValueError(f"Invalid tick size: {tick_size}. Tick size must be > 0.")


class ExperimentMatrixBuilder:
    """
    Wave-53: Deterministic matrix expander.

    Expansion order is fixed and stable:
    1. scenario_names
    2. tick_sizes
    3. simulation_end_overrides
    """

    @staticmethod
    def _format_end_time(end_time: Optional[int]) -> str:
        return "enddefault" if end_time is None else f"end{end_time}"

    @staticmethod
    def _build_case_name(
        scenario_name: str,
        tick_size: int,
        simulation_end_override: Optional[int],
    ) -> str:
        return f"{scenario_name}__tick{tick_size}__{ExperimentMatrixBuilder._format_end_time(simulation_end_override)}"

    @staticmethod
    def expand(matrix: ExperimentMatrix) -> List[ExperimentCase]:
        cases: List[ExperimentCase] = []

        for scenario_name in matrix.scenario_names:
            for tick_size in matrix.tick_sizes:
                for simulation_end_override in matrix.simulation_end_overrides:
                    case_name = ExperimentMatrixBuilder._build_case_name(
                        scenario_name=scenario_name,
                        tick_size=tick_size,
                        simulation_end_override=simulation_end_override,
                    )

                    cases.append(
                        ExperimentCase(
                            case_name=case_name,
                            scenario_name=scenario_name,
                            tick_size=tick_size,
                            simulation_end_override=simulation_end_override,
                        )
                    )

        return cases