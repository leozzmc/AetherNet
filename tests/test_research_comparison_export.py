import json
from pathlib import Path

import pytest

from sim.parameter_sweep import build_parameter_sweep
from sim.experiment_harness import ExperimentHarness
from sim.experiment_artifacts import write_artifact_bundle
from sim.research_comparison_export import export_comparison_artifacts
from sim.research_export_manifest import write_research_export_manifest
from sim.research_snapshot import build_research_snapshot
from sim.research_snapshot_compare import compare_research_snapshots
from sim.research_table_export import export_research_tables
from sim.sweep_aggregation import write_sweep_aggregation


def get_mock_comparison_doc() -> dict:
    return {
        "type": "research_snapshot_comparison",
        "version": "1.0",
        "left_snapshot_dir": "/left_path",
        "right_snapshot_dir": "/right_path",
        "snapshot_identity": {
            "left_snapshot_name": "base",
            "right_snapshot_name": "cand",
            "same_snapshot_name": False,
            "left_loaded_snapshot_dir": "/left_path",
            "right_loaded_snapshot_dir": "/right_path",
            "same_loaded_snapshot_dir": False,
            "left_manifest_snapshot_dir": "/left_path",
            "right_manifest_snapshot_dir": "/right_path",
            "same_manifest_snapshot_dir": False,
        },
        "aggregation_lineage": {
            "left_aggregation_source_path": "/agg.json",
            "right_aggregation_source_path": "/agg.json",
            "same_aggregation_source_path": True,
            "left_aggregation_type": "sweep_aggregation",
            "right_aggregation_type": "sweep_aggregation",
            "same_aggregation_type": True,
            "left_aggregation_version": "1.0",
            "right_aggregation_version": "1.0",
            "same_aggregation_version": True,
            "left_artifact_count": 1,
            "right_artifact_count": 1,
            "left_case_count": 2,
            "right_case_count": 3,
        },
        "row_counts": {
            "research_case_batch_table": {"left": 2, "right": 3, "delta": 1},
            "research_case_summary_table": {"left": 1, "right": 2, "delta": 1},
        },
        "copied_files": {
            "left": ["a.csv"],
            "right": ["a.csv", "b.csv"],
            "same_ordered_list": False,
            "same_file_set": False,
            "only_left": [],
            "only_right": ["b.csv"],
        },
    }


def test_basic_export_creates_files(tmp_path):
    doc = get_mock_comparison_doc()
    results = export_comparison_artifacts(doc, str(tmp_path))

    for _, path_str in results.items():
        file_path = Path(path_str)
        assert file_path.is_file()
        assert len(file_path.read_text(encoding="utf-8")) > 0


def test_deterministic_output_is_byte_identical(tmp_path):
    doc = get_mock_comparison_doc()
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    res1 = export_comparison_artifacts(doc, str(dir1))
    res2 = export_comparison_artifacts(doc, str(dir2))

    for key in res1.keys():
        assert Path(res1[key]).read_text(encoding="utf-8") == Path(
            res2[key]
        ).read_text(encoding="utf-8")


def test_csv_correctness_and_ordering(tmp_path):
    doc = get_mock_comparison_doc()
    res = export_comparison_artifacts(doc, str(tmp_path))

    rc_text = Path(res["row_counts_csv"]).read_text(encoding="utf-8").splitlines()
    assert rc_text[0] == "table,left,right,delta"
    assert rc_text[1] == "research_case_batch_table,2,3,1"
    assert rc_text[2] == "research_case_summary_table,1,2,1"

    fd_text = Path(res["files_csv"]).read_text(encoding="utf-8").splitlines()
    assert fd_text[0] == "category,value"
    assert fd_text[1] == "only_right,b.csv"


def test_files_diff_csv_has_sentinel_when_no_difference(tmp_path):
    doc = get_mock_comparison_doc()
    doc["copied_files"]["only_right"] = []
    doc["copied_files"]["same_file_set"] = True
    doc["copied_files"]["same_ordered_list"] = True

    res = export_comparison_artifacts(doc, str(tmp_path))
    fd_text = Path(res["files_csv"]).read_text(encoding="utf-8").splitlines()

    assert fd_text[0] == "category,value"
    assert fd_text[1] == "same,none"


def test_markdown_structure_and_rules(tmp_path):
    doc = get_mock_comparison_doc()
    res = export_comparison_artifacts(doc, str(tmp_path))
    md_text = Path(res["markdown"]).read_text(encoding="utf-8")

    assert "# Research Snapshot Comparison Report" in md_text
    assert "## Snapshot Identity" in md_text
    assert "## Aggregation Lineage" in md_text
    assert "## Row Count Differences" in md_text
    assert "## File Differences" in md_text
    assert "## Summary" in md_text

    assert "- Dataset differences detected" in md_text
    assert (
        "Row count differences detected in: "
        "research_case_batch_table, research_case_summary_table"
        in md_text
    )
    assert "- Aggregation lineage differs" in md_text
    assert "Snapshot identity differs in name and directory" in md_text
    assert "- **only_right:**" in md_text
    assert "  - b.csv" in md_text


def test_invalid_comparison_doc_raises(tmp_path):
    bad_doc = {
        "type": "wrong_type",
        "version": "1.0",
    }

    with pytest.raises(ValueError) as excinfo:
        export_comparison_artifacts(bad_doc, str(tmp_path))

    assert "comparison_doc type must be" in str(excinfo.value)


def test_integration_with_real_pipeline(tmp_path):
    # Snapshot A
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

    # Snapshot B
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

    comp_doc = compare_research_snapshots(snap_a, snap_b)

    export_dir = tmp_path / "comparison_export"
    res_paths = export_comparison_artifacts(comp_doc, str(export_dir))

    assert Path(res_paths["markdown"]).is_file()
    md_text = Path(res_paths["markdown"]).read_text(encoding="utf-8")

    assert "## Summary" in md_text
    assert "Snapshot identity differs in name and directory" in md_text
    assert "Row count differences detected in: research_case_batch_table" in md_text
    assert "- Aggregation lineage differs" in md_text