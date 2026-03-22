import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List

BATCH_TABLE_COLUMNS = [
    "case_name",
    "artifact_dir_name",
    "batch_label",
    "scenario_name",
    "delivery_ratio",
    "unique_delivered",
    "duplicate_deliveries",
    "store_remaining",
    "bundles_dropped_total",
]

SUMMARY_TABLE_COLUMNS = [
    "case_name",
    "batch_count",
    "scenario_names",
    "delivery_ratio_min",
    "delivery_ratio_max",
    "delivery_ratio_mean",
    "unique_delivered_min",
    "unique_delivered_max",
    "unique_delivered_mean",
    "duplicate_deliveries_min",
    "duplicate_deliveries_max",
    "duplicate_deliveries_mean",
    "store_remaining_min",
    "store_remaining_max",
    "store_remaining_mean",
    "bundles_dropped_total_min",
    "bundles_dropped_total_max",
    "bundles_dropped_total_mean",
]

REQUIRED_NUMERIC_METRICS = [
    "delivery_ratio",
    "unique_delivered",
    "duplicate_deliveries",
    "store_remaining",
]

OPTIONAL_NUMERIC_METRICS = [
    "bundles_dropped_total",
]


def _format_float(value: float) -> str:
    return f"{value:.6f}"


def _is_optional_metric_absent(value: Any) -> bool:
    return value is None or value == "" or value == {}


def _coerce_optional_numeric_metric(value: Any) -> float | None:
    """
    Accept optional metric values in these forms:
    - missing handled outside this function
    - None / "" / {} -> absent
    - int / float -> numeric
    - numeric string like "0", "1", "0.0" -> numeric

    Any other value is invalid.
    """
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
            raise ValueError(
                f"Optional metric value '{value}' is not numeric."
            ) from exc

    raise ValueError(f"Optional metric value '{value}' is not numeric.")


def _read_and_validate_aggregation(json_path: Path) -> Dict[str, Any]:
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
        raise ValueError(
            f"Invalid aggregation '{json_path}': 'cases' must be a list."
        )

    if data["case_count"] != len(cases):
        raise ValueError(
            f"Invalid aggregation '{json_path}': 'case_count' does not match "
            f"the number of case entries."
        )

    for case_index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(
                f"Invalid aggregation '{json_path}': case at index {case_index} "
                f"must be an object."
            )

        case_name = case.get("case_name")
        if not isinstance(case_name, str) or not case_name:
            raise ValueError(
                f"Invalid aggregation '{json_path}': case at index {case_index} "
                f"has invalid 'case_name'."
            )

        batches = case.get("batches")
        if not isinstance(batches, list):
            raise ValueError(
                f"Invalid aggregation '{json_path}': case '{case_name}' "
                f"must contain a 'batches' list."
            )

        for batch_index, batch in enumerate(batches):
            if not isinstance(batch, dict):
                raise ValueError(
                    f"Invalid aggregation '{json_path}': batch at index {batch_index} "
                    f"in case '{case_name}' must be an object."
                )

            for key in ["artifact_dir_name", "batch_label", "scenario_name"]:
                value = batch.get(key)
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"Invalid aggregation '{json_path}': batch {batch_index} "
                        f"in case '{case_name}' has invalid '{key}'."
                    )

            for metric in REQUIRED_NUMERIC_METRICS:
                value = batch.get(metric)
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Invalid aggregation '{json_path}': batch {batch_index} "
                        f"in case '{case_name}' missing numeric metric '{metric}'."
                    )

            for metric in OPTIONAL_NUMERIC_METRICS:
                if metric not in batch:
                    continue

                try:
                    _coerce_optional_numeric_metric(batch[metric])
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid aggregation '{json_path}': batch {batch_index} "
                        f"in case '{case_name}' has invalid optional metric '{metric}'."
                    ) from exc

    return data


def _canonicalized_cases(aggregation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized_cases: List[Dict[str, Any]] = []

    for case in aggregation_data["cases"]:
        sorted_batches = sorted(
            case["batches"],
            key=lambda batch: (batch["artifact_dir_name"], batch["batch_label"]),
        )
        normalized_cases.append(
            {
                "case_name": case["case_name"],
                "batches": sorted_batches,
            }
        )

    return sorted(normalized_cases, key=lambda case: case["case_name"])


def _stringify_optional_metric(value: Any) -> str:
    coerced = _coerce_optional_numeric_metric(value)
    if coerced is None:
        return ""

    if coerced.is_integer():
        return str(int(coerced))
    return str(coerced)


def _build_batch_table_rows(aggregation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for case in _canonicalized_cases(aggregation_data):
        case_name = case["case_name"]
        for batch in case["batches"]:
            row = {
                "case_name": case_name,
                "artifact_dir_name": batch["artifact_dir_name"],
                "batch_label": batch["batch_label"],
                "scenario_name": batch["scenario_name"],
                "delivery_ratio": _format_float(float(batch["delivery_ratio"])),
                "unique_delivered": str(batch["unique_delivered"]),
                "duplicate_deliveries": str(batch["duplicate_deliveries"]),
                "store_remaining": str(batch["store_remaining"]),
                "bundles_dropped_total": _stringify_optional_metric(
                    batch.get("bundles_dropped_total")
                ),
            }
            rows.append(row)

    return rows


def _aggregate_metric_strings(
    batches: List[Dict[str, Any]],
    metric: str,
    optional: bool = False,
) -> Dict[str, str]:
    present_values: List[float] = []

    for batch in batches:
        if metric not in batch:
            continue

        value = batch[metric]

        if optional:
            coerced = _coerce_optional_numeric_metric(value)
            if coerced is None:
                continue
            present_values.append(coerced)
            continue

        if isinstance(value, (int, float)):
            present_values.append(float(value))

    if not present_values:
        return {
            f"{metric}_min": "",
            f"{metric}_max": "",
            f"{metric}_mean": "",
        }

    return {
        f"{metric}_min": _format_float(min(present_values)),
        f"{metric}_max": _format_float(max(present_values)),
        f"{metric}_mean": _format_float(sum(present_values) / len(present_values)),
    }


def _build_summary_table_rows(aggregation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for case in _canonicalized_cases(aggregation_data):
        case_name = case["case_name"]
        batches = case["batches"]

        scenario_names = ";".join(sorted({batch["scenario_name"] for batch in batches}))

        row = {
            "case_name": case_name,
            "batch_count": str(len(batches)),
            "scenario_names": scenario_names,
        }

        for metric in REQUIRED_NUMERIC_METRICS:
            row.update(_aggregate_metric_strings(batches, metric, optional=False))

        for metric in OPTIONAL_NUMERIC_METRICS:
            row.update(_aggregate_metric_strings(batches, metric, optional=True))

        rows.append(row)

    return rows


def export_research_tables(aggregation_json_path: str, output_dir: str) -> str:
    """
    Read a Wave-63 sweep_aggregation.json and export deterministic
    research tables into output_dir.

    Writes:
      - research_case_batch_table.csv
      - research_case_summary_table.csv

    Returns the absolute output directory path.
    """
    json_path = Path(aggregation_json_path).resolve()
    aggregation_data = _read_and_validate_aggregation(json_path)

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    batch_csv_path = out_dir / "research_case_batch_table.csv"
    summary_csv_path = out_dir / "research_case_summary_table.csv"

    batch_rows = _build_batch_table_rows(aggregation_data)
    batch_output = io.StringIO()
    batch_writer = csv.DictWriter(
        batch_output,
        fieldnames=BATCH_TABLE_COLUMNS,
        lineterminator="\n",
    )
    batch_writer.writeheader()
    batch_writer.writerows(batch_rows)
    batch_csv_path.write_text(batch_output.getvalue(), encoding="utf-8")

    summary_rows = _build_summary_table_rows(aggregation_data)
    summary_output = io.StringIO()
    summary_writer = csv.DictWriter(
        summary_output,
        fieldnames=SUMMARY_TABLE_COLUMNS,
        lineterminator="\n",
    )
    summary_writer.writeheader()
    summary_writer.writerows(summary_rows)
    summary_csv_path.write_text(summary_output.getvalue(), encoding="utf-8")

    return str(out_dir)