import csv
import io
import json
from pathlib import Path
from typing import Any, Dict


def _validate_comparison_doc(doc: Dict[str, Any]) -> None:
    if not isinstance(doc, dict):
        raise ValueError("comparison_doc must be a dictionary.")

    if doc.get("type") != "research_snapshot_comparison":
        raise ValueError(
            "comparison_doc type must be 'research_snapshot_comparison'."
        )

    if doc.get("version") != "1.0":
        raise ValueError("comparison_doc version must be '1.0'.")

    for section_name in [
        "snapshot_identity",
        "aggregation_lineage",
        "row_counts",
        "copied_files",
    ]:
        section = doc.get(section_name)
        if not isinstance(section, dict):
            raise ValueError(f"comparison_doc missing required dict '{section_name}'.")

    row_counts = doc["row_counts"]
    for table_name, counts in row_counts.items():
        if not isinstance(counts, dict):
            raise ValueError(f"row_counts entry '{table_name}' must be a dict.")
        for field in ["left", "right", "delta"]:
            if field not in counts:
                raise ValueError(
                    f"row_counts entry '{table_name}' missing required field '{field}'."
                )

    copied_files = doc["copied_files"]
    for field in ["left", "right", "only_left", "only_right"]:
        if not isinstance(copied_files.get(field), list):
            raise ValueError(f"copied_files field '{field}' must be a list.")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(output.getvalue(), encoding="utf-8")


def _export_json(doc: Dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")


def _export_row_counts(doc: Dict[str, Any], path: Path) -> None:
    fieldnames = ["table", "left", "right", "delta"]
    rows = []

    for table in sorted(doc["row_counts"].keys()):
        counts = doc["row_counts"][table]
        rows.append(
            {
                "table": table,
                "left": counts["left"],
                "right": counts["right"],
                "delta": counts["delta"],
            }
        )

    _write_csv(path, fieldnames, rows)


def _export_lineage(doc: Dict[str, Any], path: Path) -> None:
    fieldnames = ["field", "left", "right", "same"]
    rows = []
    lineage = doc["aggregation_lineage"]

    fields_to_export = [
        "aggregation_source_path",
        "aggregation_type",
        "aggregation_version",
        "artifact_count",
        "case_count",
    ]

    for field in fields_to_export:
        left_val = lineage.get(f"left_{field}", "")
        right_val = lineage.get(f"right_{field}", "")
        same_val = lineage.get(f"same_{field}", left_val == right_val)

        rows.append(
            {
                "field": field,
                "left": str(left_val),
                "right": str(right_val),
                "same": str(same_val),
            }
        )

    _write_csv(path, fieldnames, rows)


def _export_identity(doc: Dict[str, Any], path: Path) -> None:
    fieldnames = ["field", "left", "right", "same"]
    rows = []
    identity = doc["snapshot_identity"]

    fields_to_export = [
        "snapshot_name",
        "loaded_snapshot_dir",
        "manifest_snapshot_dir",
    ]

    for field in fields_to_export:
        left_val = identity.get(f"left_{field}", "")
        right_val = identity.get(f"right_{field}", "")
        same_val = identity.get(f"same_{field}", left_val == right_val)

        rows.append(
            {
                "field": field,
                "left": str(left_val),
                "right": str(right_val),
                "same": str(same_val),
            }
        )

    _write_csv(path, fieldnames, rows)


def _export_files_diff(doc: Dict[str, Any], path: Path) -> None:
    fieldnames = ["category", "value"]
    rows = []
    copied_files = doc["copied_files"]

    only_left = sorted(copied_files.get("only_left", []))
    only_right = sorted(copied_files.get("only_right", []))

    for value in only_left:
        rows.append({"category": "only_left", "value": value})

    for value in only_right:
        rows.append({"category": "only_right", "value": value})

    if not rows:
        rows.append({"category": "same", "value": "none"})

    _write_csv(path, fieldnames, rows)


def _aggregation_lineage_is_identical(lineage: Dict[str, Any]) -> bool:
    return (
        lineage.get("same_aggregation_source_path", False)
        and lineage.get("same_aggregation_type", False)
        and lineage.get("same_aggregation_version", False)
        and lineage.get("left_artifact_count") == lineage.get("right_artifact_count")
        and lineage.get("left_case_count") == lineage.get("right_case_count")
    )


def _export_markdown(doc: Dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Research Snapshot Comparison Report")
    lines.append("")

    identity = doc["snapshot_identity"]
    lineage = doc["aggregation_lineage"]
    row_counts = doc["row_counts"]
    copied_files = doc["copied_files"]

    # Snapshot Identity
    lines.append("## Snapshot Identity")
    lines.append("")
    lines.append("| Field | Left | Right | Same |")
    lines.append("|---|---|---|---|")
    for field in ["snapshot_name", "loaded_snapshot_dir", "manifest_snapshot_dir"]:
        left_val = identity.get(f"left_{field}", "")
        right_val = identity.get(f"right_{field}", "")
        same_val = identity.get(f"same_{field}", left_val == right_val)
        lines.append(f"| {field} | {left_val} | {right_val} | {same_val} |")
    lines.append("")

    # Aggregation Lineage
    lines.append("## Aggregation Lineage")
    lines.append("")
    lines.append("| Field | Left | Right | Same |")
    lines.append("|---|---|---|---|")
    for field in [
        "aggregation_source_path",
        "aggregation_type",
        "aggregation_version",
        "artifact_count",
        "case_count",
    ]:
        left_val = lineage.get(f"left_{field}", "")
        right_val = lineage.get(f"right_{field}", "")
        same_val = lineage.get(f"same_{field}", left_val == right_val)
        lines.append(f"| {field} | {left_val} | {right_val} | {same_val} |")
    lines.append("")

    # Row Count Differences
    lines.append("## Row Count Differences")
    lines.append("")
    lines.append("| Table | Left | Right | Delta |")
    lines.append("|---|---|---|---|")

    changed_tables: list[str] = []
    for table in sorted(row_counts.keys()):
        counts = row_counts[table]
        delta = counts["delta"]
        lines.append(
            f"| {table} | {counts['left']} | {counts['right']} | {delta} |"
        )
        if delta != 0:
            changed_tables.append(table)
    lines.append("")

    # File Differences
    lines.append("## File Differences")
    lines.append("")
    only_left = sorted(copied_files.get("only_left", []))
    only_right = sorted(copied_files.get("only_right", []))

    if not only_left and not only_right:
        lines.append("- No file differences detected.")
    else:
        if only_left:
            lines.append("- **only_left:**")
            for value in only_left:
                lines.append(f"  - {value}")
        if only_right:
            lines.append("- **only_right:**")
            for value in only_right:
                lines.append(f"  - {value}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")

    if not changed_tables and not only_left and not only_right:
        lines.append("- Datasets appear structurally identical")
    else:
        lines.append("- Dataset differences detected")

    if changed_tables:
        lines.append(
            f"- Row count differences detected in: {', '.join(changed_tables)}"
        )
    else:
        lines.append("- No row count differences detected")

    if _aggregation_lineage_is_identical(lineage):
        lines.append("- Aggregation lineage is identical")
    else:
        lines.append("- Aggregation lineage differs")

    same_snapshot_name = identity.get("same_snapshot_name", False)
    same_loaded_snapshot_dir = identity.get("same_loaded_snapshot_dir", False)

    if same_snapshot_name and same_loaded_snapshot_dir:
        lines.append("- Snapshot identity is identical")
    else:
        diff_reasons: list[str] = []
        if not same_snapshot_name:
            diff_reasons.append("name")
        if not same_loaded_snapshot_dir:
            diff_reasons.append("directory")
        lines.append(f"- Snapshot identity differs in {' and '.join(diff_reasons)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_comparison_artifacts(
    comparison_doc: Dict[str, Any],
    output_dir: str,
    prefix: str = "comparison",
) -> Dict[str, str]:
    """
    Wave-70: Export a Wave-69 comparison document into deterministic, portable,
    human-readable, and analysis-friendly file artifacts.
    """
    _validate_comparison_doc(comparison_doc)

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    result_paths = {
        "json": str(out_dir / f"{prefix}.json"),
        "row_counts_csv": str(out_dir / f"{prefix}_row_counts.csv"),
        "aggregation_csv": str(out_dir / f"{prefix}_aggregation_lineage.csv"),
        "identity_csv": str(out_dir / f"{prefix}_snapshot_identity.csv"),
        "files_csv": str(out_dir / f"{prefix}_copied_files_diff.csv"),
        "markdown": str(out_dir / f"{prefix}_report.md"),
    }

    _export_json(comparison_doc, Path(result_paths["json"]))
    _export_row_counts(comparison_doc, Path(result_paths["row_counts_csv"]))
    _export_lineage(comparison_doc, Path(result_paths["aggregation_csv"]))
    _export_identity(comparison_doc, Path(result_paths["identity_csv"]))
    _export_files_diff(comparison_doc, Path(result_paths["files_csv"]))
    _export_markdown(comparison_doc, Path(result_paths["markdown"]))

    return result_paths