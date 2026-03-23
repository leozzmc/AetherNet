import json
from pathlib import Path
from typing import Any, Dict, List

from sim.research_snapshot_query import (
    get_snapshot_aggregation_metadata,
    get_snapshot_export_row_counts,
    list_snapshot_files,
    load_research_snapshot,
    validate_snapshot_completeness,
)


def discover_research_snapshots(snapshot_root_dir: str) -> List[str]:
    """
    Wave-71: Discover valid snapshot directories under snapshot_root_dir.
    Returns deterministically ordered absolute directory paths.
    """
    root_path = Path(snapshot_root_dir).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Snapshot root directory does not exist: {root_path}")

    candidates = [
        path
        for path in root_path.iterdir()
        if path.is_dir() and path.name.startswith("snapshot_")
    ]
    candidates.sort(key=lambda path: path.name)

    return [str(path.resolve()) for path in candidates]


def build_research_snapshot_registry(snapshot_root_dir: str) -> Dict[str, Any]:
    """
    Wave-71: Discover, validate, and index Wave-67 snapshots under snapshot_root_dir.
    Returns a deterministic registry document.
    """
    root_path = Path(snapshot_root_dir).resolve()
    candidate_paths = discover_research_snapshots(str(root_path))

    snapshots_data: List[Dict[str, Any]] = []

    for path_str in candidate_paths:
        snap_data = load_research_snapshot(path_str)
        validate_snapshot_completeness(snap_data)

        snapshot_manifest = snap_data["snapshot_manifest"]
        aggregation_metadata = get_snapshot_aggregation_metadata(snap_data)
        row_counts = get_snapshot_export_row_counts(snap_data)
        copied_files = list_snapshot_files(snap_data)

        snapshots_data.append(
            {
                "snapshot_name": snapshot_manifest["snapshot_name"],
                "loaded_snapshot_dir": snap_data["loaded_snapshot_dir"],
                "manifest_snapshot_dir": snapshot_manifest["snapshot_dir"],
                "aggregation_source_path": aggregation_metadata["aggregation_source_path"],
                "aggregation_type": aggregation_metadata["type"],
                "aggregation_version": aggregation_metadata["version"],
                "artifact_count": aggregation_metadata["artifact_count"],
                "case_count": aggregation_metadata["case_count"],
                "row_counts": row_counts,
                "copied_files": copied_files,
            }
        )

    return {
        "type": "research_snapshot_registry",
        "version": "1.0",
        "root_dir": str(root_path),
        "snapshot_count": len(snapshots_data),
        "snapshots": snapshots_data,
    }


def write_research_snapshot_registry(snapshot_root_dir: str) -> str:
    """
    Wave-71: Build and write research_snapshot_registry.json into snapshot_root_dir.
    Returns the absolute path to the written registry file.
    """
    registry_doc = build_research_snapshot_registry(snapshot_root_dir)

    root_path = Path(snapshot_root_dir).resolve()
    registry_file_path = root_path / "research_snapshot_registry.json"

    registry_file_path.write_text(
        json.dumps(registry_doc, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return str(registry_file_path)