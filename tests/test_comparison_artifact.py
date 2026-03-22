import json
from pathlib import Path

from sim.batch_comparison import compare_batch_dirs
from sim.comparison_artifact import build_comparison_artifact
from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentCase, ExperimentHarness


def test_build_comparison_artifact_is_deterministic(tmp_path):
    left_cases = [
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]
    right_cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]

    left_results = ExperimentHarness.run_experiments(left_cases)
    right_results = ExperimentHarness.run_experiments(right_cases)

    left_dir = tmp_path / "left_batch"
    right_dir = tmp_path / "right_batch"

    write_artifact_bundle(left_results, str(left_dir), batch_label="left")
    write_artifact_bundle(right_results, str(right_dir), batch_label="right")

    comparison = compare_batch_dirs(str(left_dir), str(right_dir))

    out_dir = tmp_path / "comparisons"

    bundle_path_1 = build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=comparison,
        output_dir=str(out_dir),
        artifact_id="run_1",
        generated_at_label="deterministic_run",
    )

    bundle_path_2 = build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=comparison,
        output_dir=str(out_dir),
        artifact_id="run_2",
        generated_at_label="deterministic_run",
    )

    path_1 = Path(bundle_path_1)
    path_2 = Path(bundle_path_2)

    for file_name in ["comparison.csv", "comparison.json", "manifest.json"]:
        assert (path_1 / file_name).exists()
        assert (path_2 / file_name).exists()
        assert (path_1 / file_name).read_text(encoding="utf-8") == (
            path_2 / file_name
        ).read_text(encoding="utf-8")


def test_build_comparison_artifact_sorts_cases_even_if_input_rows_are_unsorted(tmp_path):
    left_cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
    ]
    right_cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
    ]

    left_results = ExperimentHarness.run_experiments(left_cases)
    right_results = ExperimentHarness.run_experiments(right_cases)

    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"

    write_artifact_bundle(left_results, str(left_dir), batch_label="left_batch")
    write_artifact_bundle(right_results, str(right_dir), batch_label="right_batch")

    comparison = compare_batch_dirs(str(left_dir), str(right_dir))

    # Intentionally scramble Wave-57 output order to verify Wave-59 canonicalizes it.
    scrambled_comparison = {
        **comparison,
        "rows": list(reversed(comparison["rows"])),
    }

    out_dir = tmp_path / "out"
    bundle_path = build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=scrambled_comparison,
        output_dir=str(out_dir),
        artifact_id="sorted_check",
        generated_at_label="stable_label",
    )

    csv_text = (Path(bundle_path) / "comparison.csv").read_text(encoding="utf-8")
    csv_lines = csv_text.splitlines()

    assert csv_lines[0] == (
        "case_name,status,left_delivery_ratio,right_delivery_ratio,delivery_ratio_delta"
    )
    assert csv_lines[1].startswith("case-a,")
    assert csv_lines[2].startswith("case-b,")

    comparison_json = json.loads(
        (Path(bundle_path) / "comparison.json").read_text(encoding="utf-8")
    )
    assert comparison_json["cases"][0]["case_name"] == "case-a"
    assert comparison_json["cases"][1]["case_name"] == "case-b"


def test_manifest_structure_and_lineage(tmp_path):
    cases = [
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]
    results = ExperimentHarness.run_experiments(cases)

    left_dir = tmp_path / "left_baseline"
    right_dir = tmp_path / "right_experiment"

    write_artifact_bundle(results, str(left_dir), batch_label="left_baseline")
    write_artifact_bundle(results, str(right_dir), batch_label="right_experiment")

    comparison = compare_batch_dirs(str(left_dir), str(right_dir))

    out_dir = tmp_path / "comparison_output"
    bundle_path = build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=comparison,
        output_dir=str(out_dir),
        artifact_id="lineage_test",
        generated_at_label="test_time",
    )

    manifest = json.loads(
        (Path(bundle_path) / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["type"] == "comparison_artifact"
    assert manifest["version"] == "1.0"
    assert manifest["generated_at"] == "test_time"
    assert manifest["case_count"] == 2

    assert manifest["generated_files"] == [
        "comparison.csv",
        "comparison.json",
        "manifest.json",
    ]

    assert manifest["left_batch"]["manifest"]["batch_label"] == "left_baseline"
    assert manifest["right_batch"]["manifest"]["batch_label"] == "right_experiment"

    assert manifest["left_batch"]["path"] == str(left_dir.resolve())
    assert manifest["right_batch"]["path"] == str(right_dir.resolve())


def test_comparison_json_has_wave_59_artifact_shape(tmp_path):
    left_cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]
    right_cases = [
        ExperimentCase(case_name="case-a", scenario_name="delayed_delivery"),
    ]

    left_results = ExperimentHarness.run_experiments(left_cases)
    right_results = ExperimentHarness.run_experiments(right_cases)

    left_dir = tmp_path / "left_batch"
    right_dir = tmp_path / "right_batch"

    write_artifact_bundle(left_results, str(left_dir), batch_label="baseline")
    write_artifact_bundle(right_results, str(right_dir), batch_label="experiment")

    comparison = compare_batch_dirs(str(left_dir), str(right_dir))

    bundle_path = build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=comparison,
        output_dir=str(tmp_path / "output"),
        artifact_id="json_shape",
        generated_at_label="stable_label",
    )

    comparison_json = json.loads(
        (Path(bundle_path) / "comparison.json").read_text(encoding="utf-8")
    )

    assert comparison_json["type"] == "comparison_artifact"
    assert comparison_json["version"] == "1.0"
    assert comparison_json["left_batch_path"] == str(left_dir.resolve())
    assert comparison_json["right_batch_path"] == str(right_dir.resolve())
    assert comparison_json["case_count"] == 1

    assert len(comparison_json["cases"]) == 1
    assert comparison_json["cases"][0]["case_name"] == "case-a"
    assert comparison_json["cases"][0]["status"] == "both"
    assert "left" in comparison_json["cases"][0]
    assert "right" in comparison_json["cases"][0]
    assert "delta" in comparison_json["cases"][0]