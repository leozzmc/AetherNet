import json
from pathlib import Path

import pytest

from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.research_export_manifest import write_research_export_manifest
from sim.research_snapshot import build_research_snapshot
from sim.research_snapshot_compare import compare_research_snapshots
from sim.research_table_export import export_research_tables
from sim.sweep_aggregation import write_sweep_aggregation


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


def test_compare_identical_snapshots(tmp_path):
    snap_left = create_mock_snapshot(tmp_path, "identical_left")
    snap_right = create_mock_snapshot(tmp_path, "identical_right")

    comp = compare_research_snapshots(str(snap_left), str(snap_right))

    assert comp["type"] == "research_snapshot_comparison"
    assert comp["snapshot_identity"]["same_snapshot_name"] is False
    assert comp["aggregation_lineage"]["same_aggregation_source_path"] is True
    assert comp["aggregation_lineage"]["same_aggregation_type"] is True
    assert comp["aggregation_lineage"]["same_aggregation_version"] is True

    assert comp["row_counts"]["research_case_batch_table"]["delta"] == 0
    assert comp["row_counts"]["research_case_summary_table"]["delta"] == 0

    assert comp["copied_files"]["same_ordered_list"] is True
    assert comp["copied_files"]["same_file_set"] is True
    assert comp["copied_files"]["only_left"] == []
    assert comp["copied_files"]["only_right"] == []


def test_compare_differing_row_counts(tmp_path):
    snap_left = create_mock_snapshot(tmp_path, "left")
    snap_right = create_mock_snapshot(
        tmp_path,
        "right",
        export_overrides={
            "table_row_counts": {
                "research_case_batch_table": 15,
                "research_case_summary_table": 2,
            }
        },
    )

    comp = compare_research_snapshots(str(snap_left), str(snap_right))

    assert comp["row_counts"]["research_case_batch_table"]["left"] == 10
    assert comp["row_counts"]["research_case_batch_table"]["right"] == 15
    assert comp["row_counts"]["research_case_batch_table"]["delta"] == 5


def test_compare_differing_copied_file_declarations(tmp_path):
    snap_left = create_mock_snapshot(tmp_path, "left2")
    snap_right = create_mock_snapshot(tmp_path, "right2")

    def add_extra_file(snap_dir: Path, filename: str) -> None:
        manifest_path = snap_dir / "research_snapshot_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["copied_files"].append(filename)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (snap_dir / filename).write_text("dummy", encoding="utf-8")

    add_extra_file(snap_left, "only_in_left.txt")
    add_extra_file(snap_right, "only_in_right.pdf")

    comp = compare_research_snapshots(str(snap_left), str(snap_right))

    assert comp["copied_files"]["same_ordered_list"] is False
    assert comp["copied_files"]["same_file_set"] is False
    assert comp["copied_files"]["only_left"] == ["only_in_left.txt"]
    assert comp["copied_files"]["only_right"] == ["only_in_right.pdf"]


def test_compare_manifest_snapshot_dir_is_exposed(tmp_path):
    snap_left = create_mock_snapshot(
        tmp_path / "left_case",
        "left_case",
        overrides={"snapshot_dir": "/recorded/left"},
    )
    snap_right = create_mock_snapshot(
        tmp_path / "right_case",
        "right_case",
        overrides={"snapshot_dir": "/recorded/right"},
    )

    comp = compare_research_snapshots(str(snap_left), str(snap_right))

    assert comp["snapshot_identity"]["left_manifest_snapshot_dir"] == "/recorded/left"
    assert comp["snapshot_identity"]["right_manifest_snapshot_dir"] == "/recorded/right"
    assert comp["snapshot_identity"]["same_manifest_snapshot_dir"] is False
    assert comp["snapshot_identity"]["left_loaded_snapshot_dir"] == str(
        snap_left.resolve()
    )
    assert comp["snapshot_identity"]["right_loaded_snapshot_dir"] == str(
        snap_right.resolve()
    )


def test_invalid_snapshot_input_raises(tmp_path):
    snap_left = create_mock_snapshot(tmp_path, "left")
    snap_right = create_mock_snapshot(
        tmp_path,
        "right",
        overrides={"version": "99.9"},
    )

    with pytest.raises(ValueError) as excinfo:
        compare_research_snapshots(str(snap_left), str(snap_right))

    assert "Invalid manifest" in str(excinfo.value)


def test_deterministic_repeated_comparison(tmp_path):
    snap_left = create_mock_snapshot(tmp_path, "left")
    snap_right = create_mock_snapshot(tmp_path, "right")

    comp_1 = compare_research_snapshots(str(snap_left), str(snap_right))
    comp_2 = compare_research_snapshots(str(snap_left), str(snap_right))

    assert json.dumps(comp_1, sort_keys=True) == json.dumps(comp_2, sort_keys=True)


def test_aggregation_type_and_version_are_exposed(tmp_path):
    snap_left = create_mock_snapshot(
        tmp_path / "left_meta",
        "left_meta",
        export_overrides={
            "aggregation_source": {
                "path": "/fake/agg.json",
                "type": "sweep_aggregation",
                "version": "1.0",
                "artifact_count": 2,
                "case_count": 2,
            }
        },
    )
    snap_right = create_mock_snapshot(
        tmp_path / "right_meta",
        "right_meta",
        export_overrides={
            "aggregation_source": {
                "path": "/fake/agg.json",
                "type": "sweep_aggregation",
                "version": "1.0",
                "artifact_count": 3,
                "case_count": 4,
            }
        },
    )

    comp = compare_research_snapshots(str(snap_left), str(snap_right))

    assert comp["aggregation_lineage"]["left_aggregation_type"] == "sweep_aggregation"
    assert comp["aggregation_lineage"]["right_aggregation_type"] == "sweep_aggregation"
    assert comp["aggregation_lineage"]["same_aggregation_type"] is True
    assert comp["aggregation_lineage"]["left_aggregation_version"] == "1.0"
    assert comp["aggregation_lineage"]["right_aggregation_version"] == "1.0"
    assert comp["aggregation_lineage"]["same_aggregation_version"] is True
    assert comp["aggregation_lineage"]["left_artifact_count"] == 2
    assert comp["aggregation_lineage"]["right_artifact_count"] == 3
    assert comp["aggregation_lineage"]["left_case_count"] == 2
    assert comp["aggregation_lineage"]["right_case_count"] == 4


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-69: Full pipeline integration test ensuring Snapshot Compare Layer can
    consume and compare the outputs of the entire Phase-5 pipeline.
    """
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
    snap_a = build_research_snapshot(
        str(dir_a / "agg" / "sweep_aggregation.json"),
        str(dir_a / "export"),
        str(tmp_path / "snapshots"),
        "snap_A",
    )

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
    snap_b = build_research_snapshot(
        str(dir_b / "agg" / "sweep_aggregation.json"),
        str(dir_b / "export"),
        str(tmp_path / "snapshots"),
        "snap_B",
    )

    comp = compare_research_snapshots(snap_a, snap_b)

    assert comp["type"] == "research_snapshot_comparison"
    assert comp["aggregation_lineage"]["left_case_count"] == 1
    assert comp["aggregation_lineage"]["right_case_count"] == 2
    assert comp["aggregation_lineage"]["left_aggregation_type"] == "sweep_aggregation"
    assert comp["aggregation_lineage"]["right_aggregation_version"] == "1.0"

    assert comp["row_counts"]["research_case_batch_table"]["left"] == 1
    assert comp["row_counts"]["research_case_batch_table"]["right"] == 2
    assert comp["row_counts"]["research_case_batch_table"]["delta"] == 1