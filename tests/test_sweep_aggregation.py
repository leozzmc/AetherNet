import json
from pathlib import Path

import pytest

from sim.baseline_profiles import build_baseline_profile
from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.sweep_aggregation import aggregate_sweep_artifacts, write_sweep_aggregation


def test_aggregate_multiple_valid_artifact_bundles(tmp_path):
    artifacts_root = tmp_path / "artifacts"

    baseline_cases = build_baseline_profile("minimal_baseline")
    sweep_cases = build_parameter_sweep("minimal_baseline", {"max_steps": [50]})

    baseline_results = ExperimentHarness.run_experiments(baseline_cases)
    sweep_results = ExperimentHarness.run_experiments(sweep_cases)

    write_artifact_bundle(
        baseline_results,
        str(artifacts_root / "batch_001"),
        batch_label="baseline_run",
    )
    write_artifact_bundle(
        sweep_results,
        str(artifacts_root / "batch_002"),
        batch_label="sweep_run",
    )

    aggregation = aggregate_sweep_artifacts(str(artifacts_root))

    assert aggregation["type"] == "sweep_aggregation"
    assert aggregation["version"] == "1.0"
    assert aggregation["artifact_count"] == 2
    assert aggregation["case_count"] == 2

    case_names = [case["case_name"] for case in aggregation["cases"]]
    assert case_names == sorted(case_names)


def test_grouping_by_case_name_across_multiple_bundles(tmp_path):
    artifacts_root = tmp_path / "artifacts"

    cases = build_baseline_profile("minimal_baseline")
    results_one = ExperimentHarness.run_experiments(cases)
    results_two = ExperimentHarness.run_experiments(cases)

    write_artifact_bundle(
        results_one,
        str(artifacts_root / "batch_A"),
        batch_label="run_A",
    )
    write_artifact_bundle(
        results_two,
        str(artifacts_root / "batch_B"),
        batch_label="run_B",
    )

    aggregation = aggregate_sweep_artifacts(str(artifacts_root))

    assert aggregation["artifact_count"] == 2
    assert aggregation["case_count"] == 1

    case_entry = aggregation["cases"][0]
    assert case_entry["case_name"] == "minimal_baseline__default_multihop"
    assert len(case_entry["batches"]) == 2
    assert case_entry["batches"][0]["artifact_dir_name"] == "batch_A"
    assert case_entry["batches"][1]["artifact_dir_name"] == "batch_B"


def test_deterministic_output_is_byte_identical(tmp_path):
    artifacts_root = tmp_path / "artifacts"

    cases = build_baseline_profile("minimal_baseline")
    results = ExperimentHarness.run_experiments(cases)

    write_artifact_bundle(
        results,
        str(artifacts_root / "batch_left"),
        batch_label="left_run",
    )
    write_artifact_bundle(
        results,
        str(artifacts_root / "batch_right"),
        batch_label="right_run",
    )

    out_dir_1 = tmp_path / "out_1"
    out_dir_2 = tmp_path / "out_2"

    write_sweep_aggregation(str(artifacts_root), str(out_dir_1))
    write_sweep_aggregation(str(artifacts_root), str(out_dir_2))

    assert (out_dir_1 / "sweep_aggregation.json").read_text(encoding="utf-8") == (
        out_dir_2 / "sweep_aggregation.json"
    ).read_text(encoding="utf-8")
    assert (out_dir_1 / "sweep_aggregation.csv").read_text(encoding="utf-8") == (
        out_dir_2 / "sweep_aggregation.csv"
    ).read_text(encoding="utf-8")


def test_missing_required_file_raises(tmp_path):
    artifacts_root = tmp_path / "artifacts"
    bad_bundle = artifacts_root / "batch_bad"
    bad_bundle.mkdir(parents=True, exist_ok=True)

    (bad_bundle / "summary.csv").write_text("case_name\r\n", encoding="utf-8")
    (bad_bundle / "manifest.json").write_text("{}", encoding="utf-8")
    # intentionally missing summary.json

    with pytest.raises(ValueError) as excinfo:
        aggregate_sweep_artifacts(str(artifacts_root))

    assert "missing required file 'summary.json'" in str(excinfo.value)


def test_invalid_manifest_type_raises(tmp_path):
    artifacts_root = tmp_path / "artifacts"
    cases = build_baseline_profile("minimal_baseline")
    results = ExperimentHarness.run_experiments(cases)

    bundle_dir = artifacts_root / "batch_invalid_type"
    write_artifact_bundle(results, str(bundle_dir), batch_label="invalid_type_run")

    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["type"] = "comparison_artifact"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        aggregate_sweep_artifacts(str(artifacts_root))

    assert "manifest type must be absent or 'experiment_artifact'" in str(excinfo.value)


def test_integration_with_real_pipeline(tmp_path):
    artifacts_root = tmp_path / "artifacts"

    baseline_cases = build_baseline_profile("minimal_baseline")
    sweep_cases = build_parameter_sweep(
        "minimal_baseline",
        {"tick_size": [1, 2], "max_steps": [50]},
    )

    baseline_results = ExperimentHarness.run_experiments(baseline_cases)
    sweep_results = ExperimentHarness.run_experiments(sweep_cases)

    write_artifact_bundle(
        baseline_results,
        str(artifacts_root / "baseline_batch"),
        batch_label="baseline",
    )
    write_artifact_bundle(
        sweep_results,
        str(artifacts_root / "sweep_batch"),
        batch_label="sweep",
    )

    out_dir = tmp_path / "aggregation_out"
    write_sweep_aggregation(str(artifacts_root), str(out_dir))

    aggregation_json = json.loads(
        (out_dir / "sweep_aggregation.json").read_text(encoding="utf-8")
    )
    aggregation_csv = (out_dir / "sweep_aggregation.csv").read_text(encoding="utf-8")

    assert aggregation_json["type"] == "sweep_aggregation"
    assert aggregation_json["artifact_count"] == 2
    assert aggregation_json["case_count"] >= 2
    assert "case_name,artifact_dir_name,batch_label,scenario_name,delivery_ratio" in aggregation_csv