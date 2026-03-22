import json
from pathlib import Path
from typing import Any, Dict, List

_REQUIRED_KNOWN_FILES = [
    "research_snapshot_manifest.json",
    "research_export_manifest.json",
    "sweep_aggregation.json",
    "research_case_batch_table.csv",
    "research_case_summary_table.csv",
]


def _read_json_object(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"File not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON in '{path}' must be an object.")
    return data


def _validate_snapshot_manifest(manifest: Dict[str, Any], path: Path) -> None:
    if manifest.get("type") != "research_snapshot":
        raise ValueError(
            f"Invalid manifest '{path}': type must be 'research_snapshot'."
        )
    if manifest.get("version") != "1.0":
        raise ValueError(
            f"Invalid manifest '{path}': version must be '1.0'."
        )

    for key in [
        "snapshot_name",
        "snapshot_dir",
        "aggregation_source_path",
        "research_export_dir",
    ]:
        val = manifest.get(key)
        if not isinstance(val, str) or not val:
            raise ValueError(f"Invalid or missing '{key}' in '{path}'.")

    copied = manifest.get("copied_files")
    if not isinstance(copied, list) or not copied or not all(
        isinstance(x, str) and x for x in copied
    ):
        raise ValueError(f"Invalid or missing 'copied_files' list in '{path}'.")

    if len(set(copied)) != len(copied):
        raise ValueError(f"Duplicate entries found in 'copied_files' in '{path}'.")


def _validate_export_manifest(manifest: Dict[str, Any], path: Path) -> None:
    if manifest.get("type") != "research_export_manifest":
        raise ValueError(
            f"Invalid manifest '{path}': type must be 'research_export_manifest'."
        )
    if manifest.get("version") != "1.0":
        raise ValueError(
            f"Invalid manifest '{path}': version must be '1.0'."
        )

    counts = manifest.get("table_row_counts")
    if not isinstance(counts, dict):
        raise ValueError(f"Invalid or missing 'table_row_counts' object in '{path}'.")

    for table in ["research_case_batch_table", "research_case_summary_table"]:
        if table not in counts or not isinstance(counts[table], int):
            raise ValueError(
                f"Missing or invalid integer row count for '{table}' in '{path}'."
            )

    aggregation_source = manifest.get("aggregation_source")
    if not isinstance(aggregation_source, dict):
        raise ValueError(
            f"Invalid or missing 'aggregation_source' object in '{path}'."
        )

    if not isinstance(aggregation_source.get("path"), str) or not aggregation_source.get(
        "path"
    ):
        raise ValueError(
            f"Invalid or missing 'aggregation_source.path' in '{path}'."
        )

    if aggregation_source.get("type") != "sweep_aggregation":
        raise ValueError(
            f"Invalid 'aggregation_source.type' in '{path}': "
            "must be 'sweep_aggregation'."
        )

    if aggregation_source.get("version") != "1.0":
        raise ValueError(
            f"Invalid 'aggregation_source.version' in '{path}': must be '1.0'."
        )

    for key in ["artifact_count", "case_count"]:
        if not isinstance(aggregation_source.get(key), int):
            raise ValueError(
                f"Invalid or missing 'aggregation_source.{key}' in '{path}'."
            )


def load_research_snapshot(snapshot_dir: str) -> Dict[str, Any]:
    """
    Wave-68: Load and strictly validate a Wave-67 research snapshot directory.
    Returns a structured snapshot document.
    """
    current_dir = Path(snapshot_dir).resolve()
    if not current_dir.is_dir():
        raise ValueError(f"Snapshot directory not found: {current_dir}")

    snap_manifest_path = current_dir / "research_snapshot_manifest.json"
    exp_manifest_path = current_dir / "research_export_manifest.json"

    snap_manifest = _read_json_object(snap_manifest_path)
    _validate_snapshot_manifest(snap_manifest, snap_manifest_path)

    exp_manifest = _read_json_object(exp_manifest_path)
    _validate_export_manifest(exp_manifest, exp_manifest_path)

    return {
        "loaded_snapshot_dir": str(current_dir),
        "snapshot_manifest": snap_manifest,
        "research_export_manifest": exp_manifest,
    }


def list_snapshot_files(snapshot_data: Dict[str, Any]) -> List[str]:
    """
    Wave-68: Return the deterministic copied file list from the snapshot manifest.
    """
    return list(snapshot_data["snapshot_manifest"]["copied_files"])


def get_snapshot_aggregation_metadata(snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wave-68: Return snapshot-level aggregation metadata, merging insights from both manifests.
    The actual loaded snapshot directory is treated separately from the manifest-recorded path.
    """
    snap_man = snapshot_data["snapshot_manifest"]
    exp_man = snapshot_data["research_export_manifest"]
    agg_source = exp_man["aggregation_source"]

    return {
        "aggregation_source_path": snap_man["aggregation_source_path"],
        "type": agg_source["type"],
        "version": agg_source["version"],
        "artifact_count": agg_source["artifact_count"],
        "case_count": agg_source["case_count"],
    }


def get_snapshot_export_row_counts(snapshot_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Wave-68: Return the Wave-65 table row counts from research_export_manifest.json.
    """
    return dict(snapshot_data["research_export_manifest"]["table_row_counts"])


def validate_snapshot_completeness(snapshot_data: Dict[str, Any]) -> None:
    """
    Wave-68: Validate that all declared copied_files exist in the snapshot directory
    and that required known files are present and declared.
    Raise ValueError on inconsistency.
    """
    snapshot_dir = Path(snapshot_data["loaded_snapshot_dir"])
    copied_files = list_snapshot_files(snapshot_data)

    # 1. Every manifest-declared copied file must physically exist
    for filename in copied_files:
        if not (snapshot_dir / filename).is_file():
            raise ValueError(f"Declared file missing from snapshot: {filename}")

    # 2. Required known files must exist physically
    for filename in _REQUIRED_KNOWN_FILES:
        if not (snapshot_dir / filename).is_file():
            raise ValueError(f"Required known file missing from snapshot: {filename}")

    # 3. Required known files must also be declared in copied_files
    for filename in _REQUIRED_KNOWN_FILES:
        if filename not in copied_files:
            raise ValueError(
                f"Required known file not declared in copied_files: {filename}"
            )