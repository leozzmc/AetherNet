import json
from pathlib import Path
from typing import Any, Dict, List

from sim.artifact_catalog import read_artifact_bundle
from sim.comparison_export import write_comparison_csv


def _sorted_comparison_rows(comparison_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = comparison_result.get("rows", [])
    return sorted(rows, key=lambda row: str(row.get("case_name", "")))


def _status_from_row(row: Dict[str, Any]) -> str:
    left_present = bool(row.get("left_present", False))
    right_present = bool(row.get("right_present", False))

    if left_present and right_present:
        return "both"
    if left_present and not right_present:
        return "only_left"
    if not left_present and right_present:
        return "only_right"
    return "neither"


def _build_json_case_entry(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_name": row.get("case_name"),
        "status": _status_from_row(row),
        "left": row.get("left_raw"),
        "right": row.get("right_raw"),
        "delta": {
            "delivery_ratio": row.get("delivery_ratio_delta"),
        },
    }


def _build_normalized_comparison(
    left_batch_path: str,
    right_batch_path: str,
    comparison_result: Dict[str, Any],
) -> Dict[str, Any]:
    sorted_rows = _sorted_comparison_rows(comparison_result)

    return {
        "left_batch_dir": str(Path(left_batch_path).resolve()),
        "right_batch_dir": str(Path(right_batch_path).resolve()),
        "total_cases_compared": len(sorted_rows),
        "rows": sorted_rows,
    }


def _build_comparison_json_document(
    left_batch_path: str,
    right_batch_path: str,
    normalized_comparison: Dict[str, Any],
) -> Dict[str, Any]:
    rows = normalized_comparison.get("rows", [])

    return {
        "type": "comparison_artifact",
        "version": "1.0",
        "left_batch_path": str(Path(left_batch_path).resolve()),
        "right_batch_path": str(Path(right_batch_path).resolve()),
        "case_count": len(rows),
        "cases": [_build_json_case_entry(row) for row in rows],
    }


def _build_manifest_document(
    left_batch_path: str,
    right_batch_path: str,
    left_manifest: Dict[str, Any],
    right_manifest: Dict[str, Any],
    case_count: int,
    generated_at_label: str,
) -> Dict[str, Any]:
    return {
        "type": "comparison_artifact",
        "version": "1.0",
        "left_batch": {
            "path": str(Path(left_batch_path).resolve()),
            "manifest": left_manifest,
        },
        "right_batch": {
            "path": str(Path(right_batch_path).resolve()),
            "manifest": right_manifest,
        },
        "generated_at": generated_at_label,
        "case_count": case_count,
        "generated_files": [
            "comparison.csv",
            "comparison.json",
            "manifest.json",
        ],
    }


def build_comparison_artifact(
    left_batch_path: str,
    right_batch_path: str,
    comparison_result: Dict[str, Any],
    output_dir: str,
    artifact_id: str = "default",
    generated_at_label: str = "deterministic_run",
) -> str:
    """
    Wave-59: deterministically package a comparison result into a reproducible
    comparison artifact bundle.

    Output structure:

        comparison_<artifact_id>/
            comparison.csv
            comparison.json
            manifest.json

    Returns the absolute path to the generated comparison artifact directory.
    """
    bundle_dir = Path(output_dir).resolve() / f"comparison_{artifact_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    csv_path = bundle_dir / "comparison.csv"
    json_path = bundle_dir / "comparison.json"
    manifest_path = bundle_dir / "manifest.json"

    normalized_comparison = _build_normalized_comparison(
        left_batch_path=left_batch_path,
        right_batch_path=right_batch_path,
        comparison_result=comparison_result,
    )

    write_comparison_csv(normalized_comparison, str(csv_path))

    comparison_json_document = _build_comparison_json_document(
        left_batch_path=left_batch_path,
        right_batch_path=right_batch_path,
        normalized_comparison=normalized_comparison,
    )
    json_path.write_text(
        json.dumps(comparison_json_document, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    left_manifest = read_artifact_bundle(left_batch_path)
    right_manifest = read_artifact_bundle(right_batch_path)

    manifest_document = _build_manifest_document(
        left_batch_path=left_batch_path,
        right_batch_path=right_batch_path,
        left_manifest=left_manifest,
        right_manifest=right_manifest,
        case_count=normalized_comparison["total_cases_compared"],
        generated_at_label=generated_at_label,
    )
    manifest_path.write_text(
        json.dumps(manifest_document, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return str(bundle_dir)