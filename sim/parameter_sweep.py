from dataclasses import replace
from itertools import product
from typing import Any, Dict, List

from sim.baseline_profiles import build_baseline_profile
from sim.experiment_harness import ExperimentCase

_SUPPORTED_PARAMETERS = ("max_steps", "tick_size")
_CANONICAL_PARAMETER_ORDER = ("max_steps", "tick_size")


def _validate_and_normalize_sweep_spec(sweep_spec: Dict[str, Any]) -> Dict[str, List[int]]:
    if not isinstance(sweep_spec, dict):
        raise ValueError("sweep_spec must be a dictionary.")

    if not sweep_spec:
        raise ValueError("sweep_spec cannot be empty.")

    normalized: Dict[str, List[int]] = {}

    for parameter_name in sorted(sweep_spec.keys()):
        if parameter_name not in _SUPPORTED_PARAMETERS:
            raise ValueError(
                f"Unsupported sweep parameter: '{parameter_name}'. "
                f"Supported parameters: {list(_SUPPORTED_PARAMETERS)}"
            )

        values = sweep_spec[parameter_name]
        if not isinstance(values, list):
            raise ValueError(f"Parameter '{parameter_name}' must be a list of values.")

        if not values:
            raise ValueError(f"Parameter '{parameter_name}' cannot be an empty list.")

        normalized_values: List[int] = []
        seen_values = set()

        for value in values:
            if type(value) is not int:
                raise ValueError(
                    f"Parameter '{parameter_name}' values must be strict integers. "
                    f"Got: {type(value).__name__}"
                )

            if value <= 0:
                raise ValueError(
                    f"Parameter '{parameter_name}' values must be positive integers. "
                    f"Got: {value}"
                )

            if value in seen_values:
                raise ValueError(
                    f"Parameter '{parameter_name}' contains duplicate value: {value}"
                )

            seen_values.add(value)
            normalized_values.append(value)

        normalized[parameter_name] = sorted(normalized_values)

    return normalized


def _build_case_name(
    base_case: ExperimentCase,
    tick_size: int,
    simulation_end_override: int | None,
    normalized_sweep_spec: Dict[str, List[int]],
) -> str:
    name_parts = [base_case.case_name]

    if "max_steps" in normalized_sweep_spec:
        name_parts.append(f"max_steps{simulation_end_override}")

    if "tick_size" in normalized_sweep_spec:
        name_parts.append(f"tick_size{tick_size}")

    return "__".join(name_parts)


def build_parameter_sweep(
    profile_name: str,
    sweep_spec: Dict[str, Any],
) -> List[ExperimentCase]:
    """
    Build a deterministically ordered list of ExperimentCase objects by expanding
    the requested baseline profile with the given sweep spec.

    Raises ValueError for invalid profile names, unsupported parameters,
    invalid values, or malformed sweep specs.
    """
    normalized_sweep_spec = _validate_and_normalize_sweep_spec(sweep_spec)

    baseline_cases = sorted(
        build_baseline_profile(profile_name),
        key=lambda case: case.case_name,
    )

    swept_cases: List[ExperimentCase] = []

    for base_case in baseline_cases:
        parameter_value_lists: List[List[int]] = []

        for parameter_name in _CANONICAL_PARAMETER_ORDER:
            if parameter_name in normalized_sweep_spec:
                parameter_value_lists.append(normalized_sweep_spec[parameter_name])
            elif parameter_name == "max_steps":
                parameter_value_lists.append([base_case.simulation_end_override])
            elif parameter_name == "tick_size":
                parameter_value_lists.append([base_case.tick_size])

        for max_steps_value, tick_size_value in product(*parameter_value_lists):
            new_case_name = _build_case_name(
                base_case=base_case,
                tick_size=tick_size_value,
                simulation_end_override=max_steps_value,
                normalized_sweep_spec=normalized_sweep_spec,
            )

            swept_cases.append(
                replace(
                    base_case,
                    case_name=new_case_name,
                    tick_size=tick_size_value,
                    simulation_end_override=max_steps_value,
                )
            )

    return swept_cases