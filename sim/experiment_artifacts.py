import json
from pathlib import Path
from typing import Any, Dict, List

from sim.experiment_harness import ExperimentHarness, ExperimentResult
from sim.experiment_export import EXPORT_COLUMNS, results_to_csv_string


def results_to_summary_json(results: List[ExperimentResult]) -> str:
    """
    Wave-55: Serializes the deterministic comparison summary into a JSON string.
    Uses sort_keys=True to guarantee byte-for-byte deterministic output.
    """
    summary_dict = ExperimentHarness.generate_summary(results)
    return json.dumps(summary_dict, indent=2, sort_keys=True)


def build_artifact_manifest(
    results: List[ExperimentResult], 
    batch_label: str = "default_batch"
) -> Dict[str, Any]:
    """
    Builds a deterministic manifest describing the experiment artifact bundle.
    Does NOT use system clock or non-deterministic values.
    """
    return {
        "artifact_version": "1.0",
        "batch_label": batch_label,
        "total_cases": len(results),
        "case_names": [r.case_name for r in results],
        "generated_files": ["summary.csv", "summary.json", "manifest.json"],
        "column_order": EXPORT_COLUMNS,
    }


def write_artifact_bundle(
    results: List[ExperimentResult], 
    output_dir: str, 
    batch_label: str = "default_batch"
) -> Dict[str, str]:
    """
    Writes a complete, deterministic artifact bundle to the specified directory.
    Reuses Wave-54 export logic for the CSV component.
    
    Returns a dictionary containing the absolute paths of the written files.
    """
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    csv_path = out_path / "summary.csv"
    json_path = out_path / "summary.json"
    manifest_path = out_path / "manifest.json"

    # Write CSV using Wave-54 helper
    csv_content = results_to_csv_string(results)
    csv_path.write_text(csv_content, encoding="utf-8")

    # Write Summary JSON
    json_content = results_to_summary_json(results)
    json_path.write_text(json_content, encoding="utf-8")

    # Write Manifest JSON
    manifest_dict = build_artifact_manifest(results, batch_label)
    manifest_content = json.dumps(manifest_dict, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_content, encoding="utf-8")

    return {
        "summary_csv": str(csv_path),
        "summary_json": str(json_path),
        "manifest_json": str(manifest_path),
        "output_dir": str(out_path)
    }