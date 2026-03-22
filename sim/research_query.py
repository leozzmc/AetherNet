import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_NUMERIC_METRICS = [
    "delivery_ratio",
    "unique_delivered",
    "duplicate_deliveries",
    "store_remaining",
]

OPTIONAL_NUMERIC_METRICS = [
    "bundles_dropped_total",
]

SUPPORTED_AGGREGATES = ["min", "max", "mean"]

HIGHER_IS_BETTER_METRICS = {
    "delivery_ratio",
    "unique_delivered",
}

LOWER_IS_BETTER_METRICS = {
    "duplicate_deliveries",
    "store_remaining",
    "bundles_dropped_total",
}


def _is_optional_metric_absent(value: Any) -> bool:
    return value is None or value == "" or value == {}


def _coerce_optional_numeric_metric(value: Any) -> float | None:
    """Safely coerce optional metrics using Wave-64 boundary rules."""
    if _is_optional_metric_absent(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        try:
            return float(stripped)
        except ValueError as exc:
            raise ValueError(f"Optional metric value '{value}' is not numeric.") from exc

    raise ValueError(f"Optional metric value '{value}' is not numeric.")


def _canonicalize_aggregation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure determinism by sorting cases and batches explicitly."""
    normalized_cases: List[Dict[str, Any]] = []

    for case in data["cases"]:
        sorted_batches = sorted(
            case["batches"],
            key=lambda batch: (batch["artifact_dir_name"], batch["batch_label"]),
        )

        normalized_case = dict(case)
        normalized_case["batches"] = sorted_batches
        normalized_cases.append(normalized_case)

    normalized_data = dict(data)
    normalized_data["cases"] = sorted(
        normalized_cases,
        key=lambda case: case["case_name"],
    )
    return normalized_data


def _get_canonicalized_cases(aggregation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return _canonicalize_aggregation(aggregation_data)["cases"]


def _is_supported_metric(metric_name: str) -> bool:
    return metric_name in REQUIRED_NUMERIC_METRICS or metric_name in OPTIONAL_NUMERIC_METRICS


def _best_direction_for_metric(metric_name: str) -> bool:
    """
    Return descending=True if higher values are better, else descending=False.
    """
    if metric_name in HIGHER_IS_BETTER_METRICS:
        return True
    if metric_name in LOWER_IS_BETTER_METRICS:
        return False
    raise ValueError(f"Unsupported metric '{metric_name}'.")


def load_research_aggregation(aggregation_json_path: str) -> Dict[str, Any]:
    """
    Wave-66: Load and strictly validate a Wave-63 sweep_aggregation.json file.
    Returns the parsed and canonicalized aggregation document.
    """
    json_path = Path(aggregation_json_path).resolve()
    if not json_path.is_file():
        raise ValueError(f"Aggregation JSON not found: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{json_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON in '{json_path}' must be an object.")

    if data.get("type") != "sweep_aggregation":
        raise ValueError(
            f"Invalid aggregation '{json_path}': type must be 'sweep_aggregation'."
        )

    if data.get("version") != "1.0":
        raise ValueError(f"Invalid aggregation '{json_path}': version must be '1.0'.")

    if not isinstance(data.get("artifact_count"), int):
        raise ValueError(
            f"Invalid aggregation '{json_path}': 'artifact_count' must be an integer."
        )

    if not isinstance(data.get("case_count"), int):
        raise ValueError(
            f"Invalid aggregation '{json_path}': 'case_count' must be an integer."
        )

    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"Invalid aggregation '{json_path}': 'cases' must be a list.")

    if data["case_count"] != len(cases):
        raise ValueError(f"Invalid aggregation '{json_path}': 'case_count' mismatch.")

    for case_index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(
                f"Invalid aggregation '{json_path}': case at {case_index} must be an object."
            )

        case_name = case.get("case_name")
        if not isinstance(case_name, str) or not case_name:
            raise ValueError(
                f"Invalid aggregation '{json_path}': case at {case_index} has invalid 'case_name'."
            )

        batches = case.get("batches")
        if not isinstance(batches, list):
            raise ValueError(
                f"Invalid aggregation '{json_path}': case '{case_name}' missing 'batches'."
            )

        for batch_index, batch in enumerate(batches):
            if not isinstance(batch, dict):
                raise ValueError(
                    f"Batch {batch_index} in case '{case_name}' must be an object."
                )

            for key in ["artifact_dir_name", "batch_label", "scenario_name"]:
                value = batch.get(key)
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"Batch {batch_index} in '{case_name}' has invalid '{key}'."
                    )

            for metric in REQUIRED_NUMERIC_METRICS:
                value = batch.get(metric)
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Batch {batch_index} in '{case_name}' missing required numeric metric '{metric}'."
                    )

            for metric in OPTIONAL_NUMERIC_METRICS:
                if metric in batch:
                    try:
                        _coerce_optional_numeric_metric(batch[metric])
                    except ValueError as exc:
                        raise ValueError(
                            f"Batch {batch_index} in '{case_name}' has invalid optional metric '{metric}'."
                        ) from exc

    return _canonicalize_aggregation(data)


def find_cases_by_scenario(
    aggregation_data: Dict[str, Any],
    scenario_name: str,
) -> List[Dict[str, Any]]:
    """
    Wave-66: Return deterministically ordered case entries whose batches include scenario_name.
    """
    matching_cases = []

    for case in _get_canonicalized_cases(aggregation_data):
        for batch in case["batches"]:
            if batch.get("scenario_name") == scenario_name:
                matching_cases.append(case)
                break

    return matching_cases


def get_case_batches(
    aggregation_data: Dict[str, Any],
    case_name: str,
) -> List[Dict[str, Any]]:
    """
    Wave-66: Return deterministically ordered batch entries for case_name.
    Raise ValueError if case_name does not exist.
    """
    for case in _get_canonicalized_cases(aggregation_data):
        if case["case_name"] == case_name:
            return case["batches"]

    raise ValueError(f"Case '{case_name}' not found in aggregation data.")


def rank_cases_by_metric(
    aggregation_data: Dict[str, Any],
    metric_name: str,
    aggregate: str = "mean",
    descending: bool = True,
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Wave-66: Rank cases by a supported metric aggregated across batch entries.
    Returns deterministically ordered ranking results.
    """
    if not _is_supported_metric(metric_name):
        raise ValueError(f"Unsupported metric '{metric_name}'.")

    if aggregate not in SUPPORTED_AGGREGATES:
        raise ValueError(
            f"Unsupported aggregate mode '{aggregate}'. Supported: {SUPPORTED_AGGREGATES}"
        )

    if top_n is not None and top_n <= 0:
        raise ValueError("top_n must be a positive integer or None.")

    is_optional = metric_name in OPTIONAL_NUMERIC_METRICS
    ranked_results = []

    for case in _get_canonicalized_cases(aggregation_data):
        case_name = case["case_name"]
        valid_values: List[float] = []

        for batch in case["batches"]:
            if metric_name not in batch:
                continue

            value = batch[metric_name]

            if is_optional:
                coerced = _coerce_optional_numeric_metric(value)
                if coerced is not None:
                    valid_values.append(coerced)
            else:
                valid_values.append(float(value))

        if not valid_values:
            continue

        if aggregate == "min":
            agg_val = min(valid_values)
        elif aggregate == "max":
            agg_val = max(valid_values)
        else:
            agg_val = sum(valid_values) / len(valid_values)

        ranked_results.append(
            {
                "case_name": case_name,
                "metric_name": metric_name,
                "aggregate": aggregate,
                "metric_value": float(agg_val),
                "batch_count": len(valid_values),
            }
        )

    if not ranked_results:
        raise ValueError(f"No usable cases found for metric '{metric_name}'.")

    ranked_results.sort(
        key=lambda item: (
            -item["metric_value"] if descending else item["metric_value"],
            item["case_name"],
        )
    )

    if top_n is not None:
        return ranked_results[:top_n]
    return ranked_results


def get_best_case_by_metric(
    aggregation_data: Dict[str, Any],
    metric_name: str,
    aggregate: str = "mean",
) -> Dict[str, Any]:
    """
    Wave-66: Return the single best-ranked case entry for the given metric and aggregate mode.
    Uses metric-specific direction:
    - higher is better: delivery_ratio, unique_delivered
    - lower is better: duplicate_deliveries, store_remaining, bundles_dropped_total
    """
    descending = _best_direction_for_metric(metric_name)

    results = rank_cases_by_metric(
        aggregation_data=aggregation_data,
        metric_name=metric_name,
        aggregate=aggregate,
        descending=descending,
        top_n=1,
    )
    return results[0]