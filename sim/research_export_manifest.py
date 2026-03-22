import csv
import json
from pathlib import Path
from typing import Any, Dict


def _validate_aggregation(json_path: Path) -> Dict[str, Any]:
    if not json_path.is_file():
        raise ValueError(f"Aggregation JSON not found: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{json_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON in '{json_path}' must be an object.")

    if data.get("type") != "sweep_aggregation":
        raise ValueError(f"Invalid aggregation '{json_path}': type must be 'sweep_aggregation'.")

    if data.get("version") != "1.0":
        raise ValueError(f"Invalid aggregation '{json_path}': version must be '1.0'.")

    if "artifact_count" not in data or not isinstance(data["artifact_count"], int):
        raise ValueError(f"Invalid aggregation '{json_path}': 'artifact_count' must be an integer.")

    if "case_count" not in data or not isinstance(data["case_count"], int):
        raise ValueError(f"Invalid aggregation '{json_path}': 'case_count' must be an integer.")

    if "cases" not in data or not isinstance(data["cases"], list):
        raise ValueError(f"Invalid aggregation '{json_path}': 'cases' must be a list.")

    return data


def _count_csv_data_rows(csv_path: Path) -> int:
    """
    Count data rows in CSV deterministically.

    Definition:
    - first row = header
    - count only non-empty rows after header
    - streaming (no full file load)
    """
    if not csv_path.is_file():
        raise ValueError(f"Required research table missing: {csv_path}")
    count = 0
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        # skip header
        try:
            next(reader)
        except StopIteration:
            return 0
        for row in reader:
            # skip empty rows
            if not row or all(cell.strip() == "" for cell in row):
                continue
            count += 1
    return count


def write_research_export_manifest(aggregation_json_path: str, research_export_dir: str) -> str:
    """
    Wave-65: Validate the aggregation input and the Wave-64 research export directory,
    then write a deterministic research_export_manifest.json to establish data lineage.

    Returns the absolute path to the written manifest file.
    """
    agg_path = Path(aggregation_json_path).resolve()
    agg_data = _validate_aggregation(agg_path)

    export_dir = Path(research_export_dir).resolve()
    if not export_dir.is_dir():
        raise ValueError(f"Research export directory does not exist: {export_dir}")

    batch_csv_name = "research_case_batch_table.csv"
    summary_csv_name = "research_case_summary_table.csv"
    manifest_name = "research_export_manifest.json"

    batch_csv_path = export_dir / batch_csv_name
    summary_csv_path = export_dir / summary_csv_name

    # Validate existence and dynamically count rows
    batch_rows = _count_csv_data_rows(batch_csv_path)
    summary_rows = _count_csv_data_rows(summary_csv_path)

    manifest_data = {
        "type": "research_export_manifest",
        "version": "1.0",
        "aggregation_source": {
            "path": str(agg_path),
            "type": "sweep_aggregation",
            "version": "1.0",
            "artifact_count": agg_data["artifact_count"],
            "case_count": agg_data["case_count"],
        },
        "research_export_dir": str(export_dir),
        "generated_files": [
            batch_csv_name,
            summary_csv_name,
            manifest_name,
        ],
        "table_row_counts": {
            "research_case_batch_table": batch_rows,
            "research_case_summary_table": summary_rows,
        }
    }

    manifest_path = export_dir / manifest_name
    
    # Write deterministically using sort_keys=True
    manifest_path.write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True), 
        encoding="utf-8"
    )

    return str(manifest_path)