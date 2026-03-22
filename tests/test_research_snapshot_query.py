import json
from pathlib import Path

import pytest

from sim.parameter_sweep import build_parameter_sweep
from sim.experiment_harness import ExperimentHarness
from sim.experiment_artifacts import write_artifact_bundle
from sim.sweep_aggregation import write_sweep_aggregation
from sim.research_table_export import export_research_tables
from sim.research_export_manifest import write_research_export_manifest
from sim.research_snapshot import build_research_snapshot

from sim.research_snapshot_query import (
    get_snapshot_aggregation_metadata,
    get_snapshot_export_row_counts,
    list_snapshot_files,
    load_research_snapshot,
    validate_snapshot_completeness,
)


def create_mock_snapshot(
    path: Path,
    overrides: dict | None = None,
    export_overrides: dict | None = None,
) -> Path:
    """Helper to generate a mock Snapshot Bundle for isolated testing."""
    snap_dir = path / "snapshot_mock"
    snap_dir.mkdir(parents=True, exist_ok=True)

    snap_manifest = {
        "type": "research_snapshot",
        "version": "1.0",
        "snapshot_name": "mock",
        "snapshot_dir": str(snap_dir),
        "aggregation_source_path": "/fake/agg.json",
        "research_export_dir": "/fake/export",
        "copied_files": [
            "research_case_batch_table.csv",
            "research_case_summary_table.csv",
            "research_export_manifest.json",
            "research_snapshot_manifest.json",
            "sweep_aggregation.json",
        ],
    }
    if overrides:
        snap_manifest.update(overrides)

    export_manifest = {
        "type": "research_export_manifest",
        "version": "1.0",
        "table_row_counts": {
            "research_case_batch_table": 10,
            "research_case_summary_table": 2,
        },
        "aggregation_source": {
            "path": "/fake/agg.json",
            "type": "sweep_aggregation",
            "version": "1.0",
            "artifact_count": 2,
            "case_count": 2,
        },
    }
    if export_overrides:
        export_manifest.update(export_overrides)

    (snap_dir / "research_snapshot_manifest.json").write_text(
        json.dumps(snap_manifest),
        encoding="utf-8",
    )
    (snap_dir / "research_export_manifest.json").write_text(
        json.dumps(export_manifest),
        encoding="utf-8",
    )
    (snap_dir / "sweep_aggregation.json").write_text("{}", encoding="utf-8")
    (snap_dir / "research_case_batch_table.csv").write_text("dummy", encoding="utf-8")
    (snap_dir / "research_case_summary_table.csv").write_text(
        "dummy",
        encoding="utf-8",
    )

    return snap_dir


def test_load_real_snapshot_and_list_files(tmp_path):
    snap_dir = create_mock_snapshot(tmp_path)

    snap_data = load_research_snapshot(str(snap_dir))

    assert snap_data["loaded_snapshot_dir"] == str(snap_dir.resolve())
    assert "snapshot_manifest" in snap_data
    assert "research_export_manifest" in snap_data

    files = list_snapshot_files(snap_data)
    assert len(files) == 5
    assert "sweep_aggregation.json" in files
    assert files == snap_data["snapshot_manifest"]["copied_files"]


def test_get_aggregation_metadata(tmp_path):
    snap_dir = create_mock_snapshot(tmp_path)
    snap_data = load_research_snapshot(str(snap_dir))

    meta = get_snapshot_aggregation_metadata(snap_data)

    assert meta["aggregation_source_path"] == "/fake/agg.json"
    assert meta["type"] == "sweep_aggregation"
    assert meta["version"] == "1.0"
    assert meta["artifact_count"] == 2
    assert meta["case_count"] == 2


def test_get_export_row_counts(tmp_path):
    snap_dir = create_mock_snapshot(tmp_path)
    snap_data = load_research_snapshot(str(snap_dir))

    counts = get_snapshot_export_row_counts(snap_data)

    assert counts["research_case_batch_table"] == 10
    assert counts["research_case_summary_table"] == 2


def test_missing_declared_file_raises(tmp_path):
    snap_dir = create_mock_snapshot(tmp_path)
    snap_data = load_research_snapshot(str(snap_dir))

    (snap_dir / "sweep_aggregation.json").unlink()

    with pytest.raises(ValueError) as excinfo:
        validate_snapshot_completeness(snap_data)

    assert "Declared file missing from snapshot: sweep_aggregation.json" in str(
        excinfo.value
    )


def test_required_known_file_not_declared_raises(tmp_path):
    snap_dir = create_mock_snapshot(
        tmp_path,
        overrides={
            "copied_files": [
                "research_case_batch_table.csv",
                "research_case_summary_table.csv",
                "research_export_manifest.json",
                "research_snapshot_manifest.json",
            ]
        },
    )
    snap_data = load_research_snapshot(str(snap_dir))

    with pytest.raises(ValueError) as excinfo:
        validate_snapshot_completeness(snap_data)

    assert "Required known file not declared in copied_files: sweep_aggregation.json" in str(
        excinfo.value
    )


def test_invalid_snapshot_manifest_raises(tmp_path):
    snap_dir_1 = create_mock_snapshot(tmp_path / "1", overrides={"type": "bad_type"})
    with pytest.raises(ValueError) as excinfo1:
        load_research_snapshot(str(snap_dir_1))
    assert "type must be 'research_snapshot'" in str(excinfo1.value)

    snap_dir_2 = create_mock_snapshot(tmp_path / "2", overrides={"version": "99.0"})
    with pytest.raises(ValueError) as excinfo2:
        load_research_snapshot(str(snap_dir_2))
    assert "version must be '1.0'" in str(excinfo2.value)


def test_invalid_export_manifest_raises(tmp_path):
    snap_dir = create_mock_snapshot(
        tmp_path,
        export_overrides={"table_row_counts": {"research_case_batch_table": "bad"}},
    )

    with pytest.raises(ValueError) as excinfo:
        load_research_snapshot(str(snap_dir))

    assert "Missing or invalid integer row count" in str(excinfo.value)


def test_invalid_export_manifest_aggregation_source_raises(tmp_path):
    snap_dir = create_mock_snapshot(
        tmp_path,
        export_overrides={"aggregation_source": "not_an_object"},
    )

    with pytest.raises(ValueError) as excinfo:
        load_research_snapshot(str(snap_dir))

    assert "Invalid or missing 'aggregation_source' object" in str(excinfo.value)


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-68: Full pipeline integration test ensuring Snapshot Query Layer can
    consume and query the outputs of the entire Phase-5 pipeline.
    """
    sweep_cases = build_parameter_sweep("minimal_baseline", {"tick_size": [1]})
    results = ExperimentHarness.run_experiments(sweep_cases)

    artifacts_dir = tmp_path / "artifacts"
    write_artifact_bundle(results, str(artifacts_dir / "batch_1"), batch_label="run_1")

    agg_dir = tmp_path / "aggregation"
    write_sweep_aggregation(str(artifacts_dir), str(agg_dir))
    agg_json = agg_dir / "sweep_aggregation.json"

    export_dir = tmp_path / "research_tables"
    export_research_tables(str(agg_json), str(export_dir))

    write_research_export_manifest(str(agg_json), str(export_dir))

    snapshot_root = tmp_path / "snapshots"
    snap_dir_str = build_research_snapshot(
        str(agg_json),
        str(export_dir),
        str(snapshot_root),
        "final_run",
    )

    snap_data = load_research_snapshot(snap_dir_str)

    validate_snapshot_completeness(snap_data)

    files = list_snapshot_files(snap_data)
    assert "research_snapshot_manifest.json" in files

    counts = get_snapshot_export_row_counts(snap_data)
    assert counts["research_case_batch_table"] == 1
    assert counts["research_case_summary_table"] == 1

    meta = get_snapshot_aggregation_metadata(snap_data)
    assert meta["artifact_count"] == 1
    assert meta["case_count"] == 1
    assert meta["aggregation_source_path"] == str(agg_json.resolve())