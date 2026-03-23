import json
from pathlib import Path

import pytest

from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.research_export_manifest import write_research_export_manifest
from sim.research_report import generate_research_report
from sim.research_snapshot import build_research_snapshot
from sim.research_table_export import export_research_tables
from sim.sweep_aggregation import write_sweep_aggregation


def create_mock_snapshot(
    path: Path,
    name: str,
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


def test_valid_report_generation(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    snap_a = create_mock_snapshot(root_dir, "A")
    snap_b = create_mock_snapshot(root_dir, "B")

    out_file = tmp_path / "research_report.md"

    report_path = generate_research_report(
        snapshot_root_dir=str(root_dir),
        left_snapshot_dir=str(snap_a),
        right_snapshot_dir=str(snap_b),
        output_path=str(out_file),
    )

    assert Path(report_path).is_file()

    content = Path(report_path).read_text(encoding="utf-8")
    assert "# AetherNet Research Report" in content
    assert "## Registry Overview" in content
    assert "## Comparison Target" in content
    assert "## Aggregation Lineage" in content
    assert "## Row Count Differences" in content
    assert "## Copied File Differences" in content
    assert "## Final Assessment" in content


def test_report_contains_ordered_registry_names(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    snap_z = create_mock_snapshot(root_dir, "Z_end")
    snap_a = create_mock_snapshot(root_dir, "A_start")

    out_file = tmp_path / "report.md"
    generate_research_report(str(root_dir), str(snap_z), str(snap_a), str(out_file))

    content = out_file.read_text(encoding="utf-8")
    idx_a = content.find("- A_start")
    idx_z = content.find("- Z_end")

    assert idx_a != -1
    assert idx_z != -1
    assert idx_a < idx_z


def test_report_detects_row_count_differences(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()

    snap_a = create_mock_snapshot(root_dir, "A")
    snap_b = create_mock_snapshot(
        root_dir,
        "B",
        export_overrides={
            "table_row_counts": {
                "research_case_batch_table": 99,
                "research_case_summary_table": 2,
            }
        },
    )

    out_file = tmp_path / "report.md"
    generate_research_report(str(root_dir), str(snap_a), str(snap_b), str(out_file))

    content = out_file.read_text(encoding="utf-8")

    assert "| research_case_batch_table | 10 | 99 | 89 |" in content
    assert "- Row count differences detected in: research_case_batch_table" in content


def test_snapshot_not_in_registry_raises(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()
    snap_a = create_mock_snapshot(root_dir, "A")

    outside_dir = tmp_path / "outside_snapshots"
    outside_dir.mkdir()
    snap_rogue = create_mock_snapshot(outside_dir, "Rogue")

    out_file = tmp_path / "report.md"

    with pytest.raises(ValueError) as excinfo:
        generate_research_report(
            str(root_dir),
            str(snap_a),
            str(snap_rogue),
            str(out_file),
        )

    assert "is not indexed in the provided registry root" in str(excinfo.value)


def test_deterministic_repeated_generation(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()
    snap_a = create_mock_snapshot(root_dir, "A")
    snap_b = create_mock_snapshot(root_dir, "B")

    out_file_1 = tmp_path / "report_1.md"
    out_file_2 = tmp_path / "report_2.md"

    generate_research_report(str(root_dir), str(snap_a), str(snap_b), str(out_file_1))
    generate_research_report(str(root_dir), str(snap_a), str(snap_b), str(out_file_2))

    assert out_file_1.read_text(encoding="utf-8") == out_file_2.read_text(
        encoding="utf-8"
    )


def test_output_parent_directory_is_created(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()
    snap_a = create_mock_snapshot(root_dir, "A")
    snap_b = create_mock_snapshot(root_dir, "B")

    out_file = tmp_path / "nested" / "reports" / "research_report.md"

    report_path = generate_research_report(
        snapshot_root_dir=str(root_dir),
        left_snapshot_dir=str(snap_a),
        right_snapshot_dir=str(snap_b),
        output_path=str(out_file),
    )

    assert Path(report_path).is_file()


def test_no_file_diff_still_explicitly_reports_only_left_and_only_right(tmp_path):
    root_dir = tmp_path / "snapshots"
    root_dir.mkdir()
    snap_a = create_mock_snapshot(root_dir, "A")
    snap_b = create_mock_snapshot(root_dir, "B")

    out_file = tmp_path / "report.md"
    generate_research_report(str(root_dir), str(snap_a), str(snap_b), str(out_file))

    content = out_file.read_text(encoding="utf-8")

    assert "### only_left" in content
    assert "### only_right" in content
    assert "### only_left\n- none" in content
    assert "### only_right\n- none" in content


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-72: Full pipeline integration test ensuring Report Generator can
    consume and summarize the outputs of the entire Phase-5 pipeline.
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

    snap_a = build_research_snapshot(
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

    snap_b = build_research_snapshot(
        str(dir_b / "agg" / "sweep_aggregation.json"),
        str(dir_b / "export"),
        str(snapshot_root),
        "B_sweep",
    )

    out_file = tmp_path / "final_report.md"
    generate_research_report(
        snapshot_root_dir=str(snapshot_root),
        left_snapshot_dir=snap_a,
        right_snapshot_dir=snap_b,
        output_path=str(out_file),
    )

    content = out_file.read_text(encoding="utf-8")

    assert "# AetherNet Research Report" in content
    assert "- Snapshot count: 2" in content
    assert "- A_baseline" in content
    assert "- B_sweep" in content

    assert "## Final Assessment" in content
    assert "- Both target snapshots are present in the registry." in content
    assert "- Aggregation lineage differs." in content
    assert "Row count differences detected in: research_case_batch_table" in content
    assert "- Overall assessment: structural differences detected between snapshots." in content