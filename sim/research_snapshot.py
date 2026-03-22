import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict


COPIED_FILES_IN_ORDER = [
    "sweep_aggregation.json",
    "research_case_batch_table.csv",
    "research_case_summary_table.csv",
    "research_export_manifest.json",
    "research_snapshot_manifest.json",
]


def _validate_snapshot_name(name: str) -> None:
    if not name:
        raise ValueError("snapshot_name cannot be empty.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            f"Invalid snapshot_name '{name}'. "
            "Only letters, numbers, underscores (_), and hyphens (-) are allowed."
        )


def _validate_aggregation(agg_path: Path) -> Dict[str, Any]:
    if not agg_path.is_file():
        raise ValueError(f"Aggregation JSON not found: {agg_path}")

    try:
        data = json.loads(agg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{agg_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON in '{agg_path}' must be an object.")

    if data.get("type") != "sweep_aggregation":
        raise ValueError(
            f"Invalid aggregation '{agg_path}': type must be 'sweep_aggregation'."
        )

    if data.get("version") != "1.0":
        raise ValueError(
            f"Invalid aggregation '{agg_path}': version must be '1.0'."
        )

    if not isinstance(data.get("artifact_count"), int):
        raise ValueError(
            f"Invalid aggregation '{agg_path}': 'artifact_count' must be an integer."
        )

    if not isinstance(data.get("case_count"), int):
        raise ValueError(
            f"Invalid aggregation '{agg_path}': 'case_count' must be an integer."
        )

    if not isinstance(data.get("cases"), list):
        raise ValueError(
            f"Invalid aggregation '{agg_path}': 'cases' must be a list."
        )

    return data


def _validate_research_export_dir(export_dir: Path) -> None:
    if not export_dir.is_dir():
        raise ValueError(f"Research export directory does not exist: {export_dir}")

    required_files = [
        "research_case_batch_table.csv",
        "research_case_summary_table.csv",
        "research_export_manifest.json",
    ]

    for req_file in required_files:
        if not (export_dir / req_file).is_file():
            raise ValueError(
                f"Required research export file missing: {export_dir / req_file}"
            )


def _prepare_snapshot_dir(snapshot_dir: Path) -> None:
    """
    Deterministic overwrite semantics:
    - if snapshot dir exists, remove it completely
    - recreate it empty
    """
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=False)


def build_research_snapshot(
    aggregation_json_path: str,
    research_export_dir: str,
    snapshot_root_dir: str,
    snapshot_name: str = "default",
) -> str:
    """
    Wave-67: Validate the aggregation input and research export directory,
    then build a deterministic research snapshot directory containing copied
    research outputs and a snapshot manifest.

    Returns the absolute path to the generated snapshot directory.
    """
    _validate_snapshot_name(snapshot_name)

    agg_path = Path(aggregation_json_path).resolve()
    _validate_aggregation(agg_path)

    export_path = Path(research_export_dir).resolve()
    _validate_research_export_dir(export_path)

    root_path = Path(snapshot_root_dir).resolve()
    snapshot_dir = root_path / f"snapshot_{snapshot_name}"

    _prepare_snapshot_dir(snapshot_dir)

    shutil.copyfile(agg_path, snapshot_dir / "sweep_aggregation.json")

    export_files = [
        "research_case_batch_table.csv",
        "research_case_summary_table.csv",
        "research_export_manifest.json",
    ]
    for filename in export_files:
        shutil.copyfile(export_path / filename, snapshot_dir / filename)

    manifest_name = "research_snapshot_manifest.json"
    manifest_data = {
        "type": "research_snapshot",
        "version": "1.0",
        "snapshot_name": snapshot_name,
        "snapshot_dir": str(snapshot_dir),
        "aggregation_source_path": str(agg_path),
        "research_export_dir": str(export_path),
        "copied_files": COPIED_FILES_IN_ORDER,
    }

    manifest_path = snapshot_dir / manifest_name
    manifest_path.write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return str(snapshot_dir)