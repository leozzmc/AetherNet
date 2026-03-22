import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List


AGGREGATION_CSV_COLUMNS = [
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


def _read_json_object(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON in '{path}' must be an object.")

    return data


def _validate_manifest(artifact_dir: Path) -> Dict[str, Any]:
    manifest_path = artifact_dir / "manifest.json"
    manifest = _read_json_object(manifest_path)

    if "type" in manifest and manifest["type"] != "experiment_artifact":
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest type must be absent or 'experiment_artifact'"
        )

    required_keys = [
        "artifact_version",
        "batch_label",
        "total_cases",
        "case_names",
        "generated_files",
        "column_order",
    ]
    for key in required_keys:
        if key not in manifest:
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"manifest missing required key '{key}'"
            )

    if not isinstance(manifest["artifact_version"], str) or not manifest["artifact_version"]:
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'artifact_version' must be a non-empty string"
        )

    if not isinstance(manifest["batch_label"], str) or not manifest["batch_label"]:
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'batch_label' must be a non-empty string"
        )

    if not isinstance(manifest["total_cases"], int):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'total_cases' must be an integer"
        )

    if not isinstance(manifest["case_names"], list) or not all(
        isinstance(name, str) for name in manifest["case_names"]
    ):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'case_names' must be a list of strings"
        )

    if not isinstance(manifest["generated_files"], list) or not all(
        isinstance(name, str) for name in manifest["generated_files"]
    ):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'generated_files' must be a list of strings"
        )

    if not isinstance(manifest["column_order"], list) or not all(
        isinstance(name, str) for name in manifest["column_order"]
    ):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest key 'column_order' must be a list of strings"
        )

    return manifest


def _validate_summary(artifact_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
    summary_path = artifact_dir / "summary.json"
    summary = _read_json_object(summary_path)

    if "total_cases" not in summary:
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "summary.json missing required key 'total_cases'"
        )

    if "cases" not in summary:
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "summary.json missing required key 'cases'"
        )

    if not isinstance(summary["total_cases"], int):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "summary key 'total_cases' must be an integer"
        )

    if not isinstance(summary["cases"], list):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "summary key 'cases' must be a list"
        )

    validated_cases: List[Dict[str, Any]] = []
    for index, case in enumerate(summary["cases"]):
        if not isinstance(case, dict):
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case at index {index} must be an object"
            )

        required_case_keys = [
            "case_name",
            "scenario_name",
            "delivery_ratio",
            "unique_delivered",
            "duplicate_deliveries",
            "bundles_dropped_total",
            "store_remaining",
        ]
        for key in required_case_keys:
            if key not in case:
                raise ValueError(
                    f"Invalid experiment artifact '{artifact_dir}': "
                    f"summary case '{case.get('case_name', index)}' missing required key '{key}'"
                )

        if not isinstance(case["case_name"], str) or not case["case_name"]:
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case at index {index} has invalid 'case_name'"
            )

        if not isinstance(case["scenario_name"], str) or not case["scenario_name"]:
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case '{case['case_name']}' has invalid 'scenario_name'"
            )

        if not isinstance(case["delivery_ratio"], (int, float)):
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case '{case['case_name']}' has invalid 'delivery_ratio'"
            )

        if not isinstance(case["unique_delivered"], int):
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case '{case['case_name']}' has invalid 'unique_delivered'"
            )

        if not isinstance(case["duplicate_deliveries"], int):
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case '{case['case_name']}' has invalid 'duplicate_deliveries'"
            )

        if not isinstance(case["store_remaining"], int):
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"summary case '{case['case_name']}' has invalid 'store_remaining'"
            )

        validated_cases.append(case)

    if summary["total_cases"] != len(validated_cases):
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "summary total_cases does not match number of cases"
        )

    manifest_case_names = list(manifest["case_names"])
    summary_case_names = [case["case_name"] for case in validated_cases]
    if manifest_case_names != summary_case_names:
        raise ValueError(
            f"Invalid experiment artifact '{artifact_dir}': "
            "manifest case_names does not match summary case order"
        )

    return summary


def _read_and_validate_experiment_artifact(artifact_dir: Path) -> Dict[str, Any]:
    required_files = ["summary.csv", "summary.json", "manifest.json"]
    for file_name in required_files:
        if not (artifact_dir / file_name).is_file():
            raise ValueError(
                f"Invalid experiment artifact '{artifact_dir}': "
                f"missing required file '{file_name}'"
            )

    manifest = _validate_manifest(artifact_dir)
    summary = _validate_summary(artifact_dir, manifest)

    return {
        "artifact_dir_name": artifact_dir.name,
        "artifact_dir_path": str(artifact_dir.resolve()),
        "manifest": manifest,
        "summary": summary,
    }


def _discover_experiment_artifacts(root_dir: str) -> List[Dict[str, Any]]:
    root_path = Path(root_dir).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Root directory does not exist: {root_path}")

    child_dirs = sorted(
        [path for path in root_path.iterdir() if path.is_dir()],
        key=lambda path: path.name,
    )

    artifacts: List[Dict[str, Any]] = []
    for artifact_dir in child_dirs:
        artifacts.append(_read_and_validate_experiment_artifact(artifact_dir))

    return artifacts


def aggregate_sweep_artifacts(root_dir: str) -> Dict[str, Any]:
    """
    Discover and aggregate experiment artifact bundles under root_dir.
    Groups results by case_name and returns a deterministic aggregation document.
    """
    artifacts = _discover_experiment_artifacts(root_dir)

    grouped_cases: Dict[str, List[Dict[str, Any]]] = {}

    for artifact in artifacts:
        artifact_dir_name = artifact["artifact_dir_name"]
        batch_label = artifact["manifest"]["batch_label"]

        for case in artifact["summary"]["cases"]:
            case_name = case["case_name"]

            entry = {
                "artifact_dir_name": artifact_dir_name,
                "batch_label": batch_label,
                "scenario_name": case["scenario_name"],
                "delivery_ratio": case["delivery_ratio"],
                "unique_delivered": case["unique_delivered"],
                "duplicate_deliveries": case["duplicate_deliveries"],
                "store_remaining": case["store_remaining"],
                "bundles_dropped_total": case["bundles_dropped_total"],
            }

            grouped_cases.setdefault(case_name, []).append(entry)

    cases: List[Dict[str, Any]] = []
    for case_name in sorted(grouped_cases.keys()):
        sorted_batches = sorted(
            grouped_cases[case_name],
            key=lambda batch: (batch["artifact_dir_name"], batch["batch_label"]),
        )
        cases.append(
            {
                "case_name": case_name,
                "batches": sorted_batches,
            }
        )

    return {
        "type": "sweep_aggregation",
        "version": "1.0",
        "root_path": str(Path(root_dir).resolve()),
        "artifact_count": len(artifacts),
        "case_count": len(cases),
        "cases": cases,
    }


def write_sweep_aggregation(root_dir: str, output_dir: str) -> str:
    """
    Build sweep aggregation outputs under output_dir.
    Writes:
      - sweep_aggregation.csv
      - sweep_aggregation.json
    Returns the absolute output directory path.
    """
    aggregation = aggregate_sweep_artifacts(root_dir)

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "sweep_aggregation.json"
    csv_path = out_dir / "sweep_aggregation.csv"

    json_path.write_text(
        json.dumps(aggregation, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=AGGREGATION_CSV_COLUMNS,
        lineterminator="\r\n",
    )
    writer.writeheader()

    for case_entry in aggregation["cases"]:
        case_name = case_entry["case_name"]
        for batch_entry in case_entry["batches"]:
            writer.writerow(
                {
                    "case_name": case_name,
                    "artifact_dir_name": batch_entry["artifact_dir_name"],
                    "batch_label": batch_entry["batch_label"],
                    "scenario_name": batch_entry["scenario_name"],
                    "delivery_ratio": batch_entry["delivery_ratio"],
                    "unique_delivered": batch_entry["unique_delivered"],
                    "duplicate_deliveries": batch_entry["duplicate_deliveries"],
                    "store_remaining": batch_entry["store_remaining"],
                    "bundles_dropped_total": batch_entry["bundles_dropped_total"],
                }
            )

    csv_path.write_text(output.getvalue(), encoding="utf-8")

    return str(out_dir)