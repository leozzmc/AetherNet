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

from sim.research_snapshot_registry import (
    build_research_snapshot_registry,
    discover_research_snapshots,
    write_research_snapshot_registry,
)


def create_mock_snapshot(
    path: Path,
    name: str,
    overrides: dict | None = None,
    export_overrides: dict | None = None,
) -> Path:
    """Helper to generate a mock Snapshot Bundle for isolated testing."""
    snap_dir = path / f"snapshot_{name}"
    snap_dir.mkdir(parents=True, exist_ok=True)

    snap_manifest = {
        "type": "research_snapshot",
        "version": "1.0",
        "snapshot_name": name,
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
    (snap_dir / "research_case_summary_table.csv").write_text("dummy", encoding="utf-8")

    return snap_dir


def test_discover_multiple_valid_snapshots(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    snap_b = create_mock_snapshot(root_dir, "B_beta")
    snap_a = create_mock_snapshot(root_dir, "A_alpha")

    discovered = discover_research_snapshots(str(root_dir))

    assert len(discovered) == 2
    assert discovered[0] == str(snap_a.resolve())
    assert discovered[1] == str(snap_b.resolve())


def test_non_snapshot_directories_and_files_are_ignored(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    snap_valid = create_mock_snapshot(root_dir, "valid")

    (root_dir / "not_a_snapshot_dir").mkdir()
    (root_dir / "snapshot_fake.txt").write_text("I am a file, not a dir")
    (root_dir / "research_snapshot_registry.json").write_text("{}", encoding="utf-8")

    discovered = discover_research_snapshots(str(root_dir))

    assert len(discovered) == 1
    assert discovered[0] == str(snap_valid.resolve())


def test_malformed_snapshot_directory_raises(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    bad_snap = root_dir / "snapshot_bad"
    bad_snap.mkdir()
    (bad_snap / "research_snapshot_manifest.json").write_text(
        '{"bad": "json"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as excinfo:
        build_research_snapshot_registry(str(root_dir))

    assert "Invalid manifest" in str(excinfo.value)


def test_build_registry_from_real_snapshots(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    create_mock_snapshot(root_dir, "one")
    create_mock_snapshot(root_dir, "two")

    registry = build_research_snapshot_registry(str(root_dir))

    assert registry["type"] == "research_snapshot_registry"
    assert registry["version"] == "1.0"
    assert registry["snapshot_count"] == 2

    snap_data = registry["snapshots"][0]
    assert snap_data["snapshot_name"] == "one"
    assert "loaded_snapshot_dir" in snap_data
    assert "manifest_snapshot_dir" in snap_data
    assert snap_data["aggregation_source_path"] == "/fake/agg.json"
    assert snap_data["artifact_count"] == 2
    assert snap_data["case_count"] == 2
    assert snap_data["row_counts"]["research_case_summary_table"] == 2

    assert snap_data["copied_files"] == [
        "research_case_batch_table.csv",
        "research_case_summary_table.csv",
        "research_export_manifest.json",
        "research_snapshot_manifest.json",
        "sweep_aggregation.json",
    ]


def test_manifest_recorded_snapshot_dir_is_preserved(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    create_mock_snapshot(
        root_dir,
        "portable_case",
        overrides={"snapshot_dir": "/recorded/portable/path"},
    )

    registry = build_research_snapshot_registry(str(root_dir))
    snap_data = registry["snapshots"][0]

    assert snap_data["snapshot_name"] == "portable_case"
    assert snap_data["loaded_snapshot_dir"] == str(
        (root_dir / "snapshot_portable_case").resolve()
    )
    assert snap_data["manifest_snapshot_dir"] == "/recorded/portable/path"


def test_write_registry_artifact_deterministic(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    create_mock_snapshot(root_dir, "stable")

    path1_str = write_research_snapshot_registry(str(root_dir))
    path2_str = write_research_snapshot_registry(str(root_dir))

    assert path1_str == path2_str

    content1 = Path(path1_str).read_text(encoding="utf-8")
    content2 = Path(path2_str).read_text(encoding="utf-8")

    assert content1 == content2

    doc = json.loads(content1)
    assert doc["snapshot_count"] == 1
    assert doc["snapshots"][0]["snapshot_name"] == "stable"


def test_existing_registry_file_does_not_break_registry_build(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    create_mock_snapshot(root_dir, "stable")
    existing_registry = root_dir / "research_snapshot_registry.json"
    existing_registry.write_text('{"old": "registry"}', encoding="utf-8")

    registry = build_research_snapshot_registry(str(root_dir))

    assert registry["snapshot_count"] == 1
    assert registry["snapshots"][0]["snapshot_name"] == "stable"


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-71: Full pipeline integration test ensuring Snapshot Registry Layer can
    index snapshots generated from the entire Phase-5 pipeline.
    """
    snapshot_root = tmp_path / "snapshots"
    snapshot_root.mkdir()

    # Build Snapshot A
    cases_a = build_parameter_sweep("minimal_baseline", {"tick_size": [1]})
    results_a = ExperimentHarness.run_experiments(cases_a)
    dir_a = tmp_path / "run_A"
    dir_a.mkdir()
    write_artifact_bundle(
        results_a,
        str(dir_a / "artifacts" / "b1"),
        batch_label="baseline",
    )
    write_sweep_aggregation(str(dir_a / "artifacts"), str(dir_a / "agg"))
    export_research_tables(
        str(dir_a / "agg" / "sweep_aggregation.json"),
        str(dir_a / "export"),
    )
    write_research_export_manifest(
        str(dir_a / "agg" / "sweep_aggregation.json"),
        str(dir_a / "export"),
    )

    build_research_snapshot(
        str(dir_a / "agg" / "sweep_aggregation.json"),
        str(dir_a / "export"),
        str(snapshot_root),
        "A_baseline",
    )

    # Build Snapshot B
    cases_b = build_parameter_sweep("minimal_baseline", {"tick_size": [1, 2]})
    results_b = ExperimentHarness.run_experiments(cases_b)
    dir_b = tmp_path / "run_B"
    dir_b.mkdir()
    write_artifact_bundle(
        results_b,
        str(dir_b / "artifacts" / "b1"),
        batch_label="sweep",
    )
    write_sweep_aggregation(str(dir_b / "artifacts"), str(dir_b / "agg"))
    export_research_tables(
        str(dir_b / "agg" / "sweep_aggregation.json"),
        str(dir_b / "export"),
    )
    write_research_export_manifest(
        str(dir_b / "agg" / "sweep_aggregation.json"),
        str(dir_b / "export"),
    )

    build_research_snapshot(
        str(dir_b / "agg" / "sweep_aggregation.json"),
        str(dir_b / "export"),
        str(snapshot_root),
        "B_sweep",
    )

    registry_path_str = write_research_snapshot_registry(str(snapshot_root))

    registry = json.loads(Path(registry_path_str).read_text(encoding="utf-8"))

    assert registry["type"] == "research_snapshot_registry"
    assert registry["snapshot_count"] == 2

    snapshots = registry["snapshots"]
    assert snapshots[0]["snapshot_name"] == "A_baseline"
    assert snapshots[1]["snapshot_name"] == "B_sweep"

    assert snapshots[0]["case_count"] == 1
    assert snapshots[1]["case_count"] == 2

    assert snapshots[1]["row_counts"]["research_case_batch_table"] == 2
    assert "loaded_snapshot_dir" in snapshots[0]
    assert "manifest_snapshot_dir" in snapshots[0]