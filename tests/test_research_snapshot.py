import json
from pathlib import Path

import pytest

from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.research_export_manifest import write_research_export_manifest
from sim.research_snapshot import build_research_snapshot
from sim.research_table_export import export_research_tables
from sim.sweep_aggregation import write_sweep_aggregation


def create_mock_upstream_data(tmp_path: Path) -> tuple[Path, Path]:
    """Helper to create mock inputs representing Wave-63 and Wave-64/65 outputs."""
    agg_dir = tmp_path / "agg"
    agg_dir.mkdir(parents=True, exist_ok=True)

    agg_data = {
        "type": "sweep_aggregation",
        "version": "1.0",
        "root_path": "/mock",
        "artifact_count": 1,
        "case_count": 1,
        "cases": [],
    }
    agg_json_path = agg_dir / "sweep_aggregation.json"
    agg_json_path.write_text(json.dumps(agg_data), encoding="utf-8")

    export_dir = tmp_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    (export_dir / "research_case_batch_table.csv").write_text(
        "dummy,csv\n",
        encoding="utf-8",
    )
    (export_dir / "research_case_summary_table.csv").write_text(
        "dummy,csv\n",
        encoding="utf-8",
    )
    (export_dir / "research_export_manifest.json").write_text(
        '{"type": "research_export_manifest"}',
        encoding="utf-8",
    )

    return agg_json_path, export_dir


def test_valid_snapshot_build(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    snapshot_dir_str = build_research_snapshot(
        aggregation_json_path=str(agg_json_path),
        research_export_dir=str(export_dir),
        snapshot_root_dir=str(snapshot_root),
        snapshot_name="test_run",
    )

    snapshot_dir = Path(snapshot_dir_str)
    assert snapshot_dir.is_dir()
    assert snapshot_dir.name == "snapshot_test_run"

    assert (snapshot_dir / "sweep_aggregation.json").is_file()
    assert (snapshot_dir / "research_case_batch_table.csv").is_file()
    assert (snapshot_dir / "research_case_summary_table.csv").is_file()
    assert (snapshot_dir / "research_export_manifest.json").is_file()
    assert (snapshot_dir / "research_snapshot_manifest.json").is_file()


def test_missing_research_export_file_raises(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    (export_dir / "research_case_summary_table.csv").unlink()

    with pytest.raises(ValueError) as excinfo:
        build_research_snapshot(
            aggregation_json_path=str(agg_json_path),
            research_export_dir=str(export_dir),
            snapshot_root_dir=str(snapshot_root),
        )
    assert "Required research export file missing" in str(excinfo.value)
    assert "research_case_summary_table.csv" in str(excinfo.value)


def test_invalid_snapshot_name_raises(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    invalid_names = ["", "../bad", "bad/name", "bad\\name", "name with space"]

    for bad_name in invalid_names:
        with pytest.raises(ValueError) as excinfo:
            build_research_snapshot(
                aggregation_json_path=str(agg_json_path),
                research_export_dir=str(export_dir),
                snapshot_root_dir=str(snapshot_root),
                snapshot_name=bad_name,
            )
        assert "snapshot_name" in str(excinfo.value)


def test_deterministic_repeated_build(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    build_research_snapshot(
        str(agg_json_path),
        str(export_dir),
        str(snapshot_root),
        "stable",
    )
    manifest_path = snapshot_root / "snapshot_stable" / "research_snapshot_manifest.json"
    manifest_content_1 = manifest_path.read_text(encoding="utf-8")

    build_research_snapshot(
        str(agg_json_path),
        str(export_dir),
        str(snapshot_root),
        "stable",
    )
    manifest_content_2 = manifest_path.read_text(encoding="utf-8")

    assert manifest_content_1 == manifest_content_2


def test_rebuild_clears_stale_files(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    snapshot_dir_str = build_research_snapshot(
        str(agg_json_path),
        str(export_dir),
        str(snapshot_root),
        "stable",
    )
    snapshot_dir = Path(snapshot_dir_str)

    stale_file = snapshot_dir / "old_debug.txt"
    stale_file.write_text("stale", encoding="utf-8")
    assert stale_file.is_file()

    build_research_snapshot(
        str(agg_json_path),
        str(export_dir),
        str(snapshot_root),
        "stable",
    )

    assert not stale_file.exists()


def test_snapshot_copies_aggregation_file_exactly(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    original_content = agg_json_path.read_text(encoding="utf-8")

    snapshot_dir_str = build_research_snapshot(
        aggregation_json_path=str(agg_json_path),
        research_export_dir=str(export_dir),
        snapshot_root_dir=str(snapshot_root),
    )

    copied_content = (Path(snapshot_dir_str) / "sweep_aggregation.json").read_text(
        encoding="utf-8"
    )
    assert copied_content == original_content


def test_manifest_copied_files_are_in_explicit_order(tmp_path):
    agg_json_path, export_dir = create_mock_upstream_data(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    snapshot_dir_str = build_research_snapshot(
        aggregation_json_path=str(agg_json_path),
        research_export_dir=str(export_dir),
        snapshot_root_dir=str(snapshot_root),
        snapshot_name="ordered",
    )

    manifest = json.loads(
        (Path(snapshot_dir_str) / "research_snapshot_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["copied_files"] == [
        "sweep_aggregation.json",
        "research_case_batch_table.csv",
        "research_case_summary_table.csv",
        "research_export_manifest.json",
        "research_snapshot_manifest.json",
    ]


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-67: Full pipeline integration test ensuring Snapshot Bundle can
    consume and package the outputs of the entire Phase-5 pipeline.
    """
    sweep_cases = build_parameter_sweep("minimal_baseline", {"tick_size": [1]})
    results = ExperimentHarness.run_experiments(sweep_cases)

    artifacts_dir = tmp_path / "artifacts"
    write_artifact_bundle(results, str(artifacts_dir / "batch_1"), batch_label="run_1")

    agg_dir = tmp_path / "aggregation"
    write_sweep_aggregation(str(artifacts_dir), str(agg_dir))
    agg_json_path = agg_dir / "sweep_aggregation.json"

    export_dir = tmp_path / "research_tables"
    export_research_tables(str(agg_json_path), str(export_dir))

    write_research_export_manifest(str(agg_json_path), str(export_dir))

    snapshot_root = tmp_path / "snapshots"
    snapshot_dir_str = build_research_snapshot(
        aggregation_json_path=str(agg_json_path),
        research_export_dir=str(export_dir),
        snapshot_root_dir=str(snapshot_root),
        snapshot_name="final_eval",
    )

    snapshot_dir = Path(snapshot_dir_str)

    assert snapshot_dir.is_dir()
    assert snapshot_dir.name == "snapshot_final_eval"

    manifest_path = snapshot_dir / "research_snapshot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["type"] == "research_snapshot"
    assert manifest["snapshot_name"] == "final_eval"
    assert "sweep_aggregation.json" in manifest["copied_files"]