from pathlib import Path
from typing import Any, Dict

from sim.research_snapshot_compare import compare_research_snapshots
from sim.research_snapshot_registry import build_research_snapshot_registry


def _validate_snapshots_in_registry(
    registry: Dict[str, Any],
    left_dir: str,
    right_dir: str,
) -> None:
    """Ensure both target snapshots are officially indexed in the given registry."""
    left_path = str(Path(left_dir).resolve())
    right_path = str(Path(right_dir).resolve())

    registered_dirs = [snap["loaded_snapshot_dir"] for snap in registry["snapshots"]]

    if left_path not in registered_dirs:
        raise ValueError(
            f"Left snapshot '{left_path}' is not indexed in the provided registry root."
        )

    if right_path not in registered_dirs:
        raise ValueError(
            f"Right snapshot '{right_path}' is not indexed in the provided registry root."
        )


def _aggregation_lineage_is_identical(lineage: Dict[str, Any]) -> bool:
    return (
        lineage.get("same_aggregation_source_path", False)
        and lineage.get("same_aggregation_type", False)
        and lineage.get("same_aggregation_version", False)
        and lineage.get("left_artifact_count") == lineage.get("right_artifact_count")
        and lineage.get("left_case_count") == lineage.get("right_case_count")
    )


def generate_research_report(
    snapshot_root_dir: str,
    left_snapshot_dir: str,
    right_snapshot_dir: str,
    output_path: str,
) -> str:
    """
    Wave-72: Build a deterministic markdown research report from a snapshot registry
    and a pairwise snapshot comparison.
    """
    registry = build_research_snapshot_registry(snapshot_root_dir)
    _validate_snapshots_in_registry(registry, left_snapshot_dir, right_snapshot_dir)

    comparison = compare_research_snapshots(left_snapshot_dir, right_snapshot_dir)

    lines: list[str] = []

    # 1. Title
    lines.append("# AetherNet Research Report")
    lines.append("")

    # 2. Registry Overview
    lines.append("## Registry Overview")
    lines.append("")
    lines.append(f"- Root: {registry['root_dir']}")
    lines.append(f"- Snapshot count: {registry['snapshot_count']}")
    lines.append("")
    lines.append("### Registered Snapshots")
    for snap in registry["snapshots"]:
        lines.append(f"- {snap['snapshot_name']}")
    lines.append("")

    # 3. Comparison Target
    identity = comparison["snapshot_identity"]
    lines.append("## Comparison Target")
    lines.append("")
    lines.append(f"- **Left Snapshot:** {identity['left_snapshot_name']}")
    lines.append(f"  - Loaded from: {identity['left_loaded_snapshot_dir']}")
    lines.append(f"- **Right Snapshot:** {identity['right_snapshot_name']}")
    lines.append(f"  - Loaded from: {identity['right_loaded_snapshot_dir']}")
    lines.append("")

    # 4. Aggregation Lineage
    lineage = comparison["aggregation_lineage"]
    lines.append("## Aggregation Lineage")
    lines.append("")
    lines.append("| Field | Left | Right | Same |")
    lines.append("|---|---|---|---|")

    fields = [
        "aggregation_source_path",
        "aggregation_type",
        "aggregation_version",
        "artifact_count",
        "case_count",
    ]
    for field in fields:
        left_val = lineage.get(f"left_{field}", "")
        right_val = lineage.get(f"right_{field}", "")
        same_val = lineage.get(f"same_{field}", left_val == right_val)
        lines.append(f"| {field} | {left_val} | {right_val} | {same_val} |")
    lines.append("")

    # 5. Row Count Differences
    row_counts = comparison["row_counts"]
    lines.append("## Row Count Differences")
    lines.append("")
    lines.append("| Table | Left | Right | Delta |")
    lines.append("|---|---|---|---|")

    changed_tables: list[str] = []
    for table in sorted(row_counts.keys()):
        counts = row_counts[table]
        delta = counts["delta"]
        lines.append(f"| {table} | {counts['left']} | {counts['right']} | {delta} |")
        if delta != 0:
            changed_tables.append(table)
    lines.append("")

    # 6. Copied File Differences
    copied_files = comparison["copied_files"]
    only_left = sorted(copied_files["only_left"])
    only_right = sorted(copied_files["only_right"])

    lines.append("## Copied File Differences")
    lines.append("")
    lines.append(f"- Ordered list is identical: {copied_files['same_ordered_list']}")
    lines.append(f"- File set is identical: {copied_files['same_file_set']}")
    lines.append("")

    lines.append("### only_left")
    if only_left:
        for value in only_left:
            lines.append(f"- {value}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("### only_right")
    if only_right:
        for value in only_right:
            lines.append(f"- {value}")
    else:
        lines.append("- none")
    lines.append("")

    # 7. Final Assessment
    lines.append("## Final Assessment")
    lines.append("")
    lines.append("- Both target snapshots are present in the registry.")

    is_lineage_identical = _aggregation_lineage_is_identical(lineage)
    if is_lineage_identical:
        lines.append("- Aggregation lineage is identical.")
    else:
        lines.append("- Aggregation lineage differs.")

    if changed_tables:
        lines.append(
            f"- Row count differences detected in: {', '.join(changed_tables)}"
        )
    else:
        lines.append("- No row count differences detected.")

    if only_left or only_right:
        lines.append("- Copied file differences detected.")
    else:
        lines.append("- Copied file differences detected: none")

    if is_lineage_identical and not changed_tables and not only_left and not only_right:
        lines.append(
            "- Overall assessment: no structural differences detected between snapshots."
        )
    else:
        lines.append(
            "- Overall assessment: structural differences detected between snapshots."
        )

    out_path = Path(output_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return str(out_path)