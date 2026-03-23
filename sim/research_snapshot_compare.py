from typing import Any, Dict

from sim.research_snapshot_query import (
    get_snapshot_aggregation_metadata,
    get_snapshot_export_row_counts,
    list_snapshot_files,
    load_research_snapshot,
    validate_snapshot_completeness,
)


def compare_research_snapshots(
    left_snapshot_dir: str,
    right_snapshot_dir: str,
) -> Dict[str, Any]:
    """
    Wave-69: Load, validate, and compare two Wave-67 research snapshots.
    Returns a deterministic comparison document.
    """
    left_data = load_research_snapshot(left_snapshot_dir)
    right_data = load_research_snapshot(right_snapshot_dir)

    validate_snapshot_completeness(left_data)
    validate_snapshot_completeness(right_data)

    left_manifest = left_data["snapshot_manifest"]
    right_manifest = right_data["snapshot_manifest"]

    left_meta = get_snapshot_aggregation_metadata(left_data)
    right_meta = get_snapshot_aggregation_metadata(right_data)

    left_counts = get_snapshot_export_row_counts(left_data)
    right_counts = get_snapshot_export_row_counts(right_data)

    left_files = list_snapshot_files(left_data)
    right_files = list_snapshot_files(right_data)

    row_counts_comparison: Dict[str, Dict[str, int]] = {}
    all_tables = sorted(set(left_counts.keys()) | set(right_counts.keys()))

    for table in all_tables:
        left_count = left_counts.get(table, 0)
        right_count = right_counts.get(table, 0)
        row_counts_comparison[table] = {
            "left": left_count,
            "right": right_count,
            "delta": right_count - left_count,
        }

    left_files_set = set(left_files)
    right_files_set = set(right_files)

    return {
        "type": "research_snapshot_comparison",
        "version": "1.0",
        "left_snapshot_dir": left_data["loaded_snapshot_dir"],
        "right_snapshot_dir": right_data["loaded_snapshot_dir"],
        "snapshot_identity": {
            "left_snapshot_name": left_manifest["snapshot_name"],
            "right_snapshot_name": right_manifest["snapshot_name"],
            "same_snapshot_name": (
                left_manifest["snapshot_name"] == right_manifest["snapshot_name"]
            ),
            "left_loaded_snapshot_dir": left_data["loaded_snapshot_dir"],
            "right_loaded_snapshot_dir": right_data["loaded_snapshot_dir"],
            "left_manifest_snapshot_dir": left_manifest["snapshot_dir"],
            "right_manifest_snapshot_dir": right_manifest["snapshot_dir"],
            "same_loaded_snapshot_dir": (
                left_data["loaded_snapshot_dir"] == right_data["loaded_snapshot_dir"]
            ),
            "same_manifest_snapshot_dir": (
                left_manifest["snapshot_dir"] == right_manifest["snapshot_dir"]
            ),
        },
        "aggregation_lineage": {
            "left_aggregation_source_path": left_meta["aggregation_source_path"],
            "right_aggregation_source_path": right_meta["aggregation_source_path"],
            "same_aggregation_source_path": (
                left_meta["aggregation_source_path"]
                == right_meta["aggregation_source_path"]
            ),
            "left_aggregation_type": left_meta["type"],
            "right_aggregation_type": right_meta["type"],
            "same_aggregation_type": left_meta["type"] == right_meta["type"],
            "left_aggregation_version": left_meta["version"],
            "right_aggregation_version": right_meta["version"],
            "same_aggregation_version": (
                left_meta["version"] == right_meta["version"]
            ),
            "left_artifact_count": left_meta["artifact_count"],
            "right_artifact_count": right_meta["artifact_count"],
            "left_case_count": left_meta["case_count"],
            "right_case_count": right_meta["case_count"],
        },
        "row_counts": row_counts_comparison,
        "copied_files": {
            "left": left_files,
            "right": right_files,
            "same_ordered_list": left_files == right_files,
            "same_file_set": left_files_set == right_files_set,
            "only_left": sorted(left_files_set - right_files_set),
            "only_right": sorted(right_files_set - left_files_set),
        },
    }