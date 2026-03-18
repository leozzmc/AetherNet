import json
from pathlib import Path

from sim.experiment_harness import ExperimentCase, ExperimentHarness, ExperimentResult
from sim.experiment_export import EXPORT_COLUMNS
from sim.experiment_artifacts import (
    results_to_summary_json,
    build_artifact_manifest,
    write_artifact_bundle,
)


def make_dummy_result(case_name: str, delivery_ratio: float) -> ExperimentResult:
    return ExperimentResult(
        case_name=case_name,
        scenario_name="test_scenario",
        final_metrics={},
        delivered_bundle_ids=["b1", "b2"],
        store_bundle_ids_remaining=["b3"],
        delivery_ratio=delivery_ratio,
        unique_delivered=2,
        duplicate_deliveries=1,
        bundles_dropped_total=0,
    )


def test_summary_json_export_is_deterministic():
    r1 = make_dummy_result("case-1", 0.5)
    r2 = make_dummy_result("case-2", 0.8)

    json_str_1 = results_to_summary_json([r1, r2])
    json_str_2 = results_to_summary_json([r1, r2])

    assert json_str_1 == json_str_2
    
    parsed = json.loads(json_str_1)
    assert parsed["total_cases"] == 2
    assert parsed["cases"][0]["case_name"] == "case-1"
    assert parsed["cases"][1]["delivery_ratio"] == 0.8


def test_manifest_content_is_deterministic():
    r1 = make_dummy_result("case-1", 0.5)
    
    manifest_1 = build_artifact_manifest([r1], batch_label="test_batch")
    manifest_2 = build_artifact_manifest([r1], batch_label="test_batch")
    
    assert manifest_1 == manifest_2
    assert manifest_1["artifact_version"] == "1.0"
    assert manifest_1["total_cases"] == 1
    assert manifest_1["case_names"] == ["case-1"]
    assert manifest_1["column_order"] == EXPORT_COLUMNS


def test_manifest_contains_stable_file_names():
    manifest = build_artifact_manifest([])
    
    assert "summary.csv" in manifest["generated_files"]
    assert "summary.json" in manifest["generated_files"]
    assert "manifest.json" in manifest["generated_files"]
    assert len(manifest["generated_files"]) == 3


def test_batch_label_handling_is_deterministic():
    r1 = make_dummy_result("case-1", 0.5)
    
    # Default behavior
    manifest_default = build_artifact_manifest([r1])
    assert manifest_default["batch_label"] == "default_batch"
    
    # Explicit override
    manifest_custom = build_artifact_manifest([r1], batch_label="sweep_001")
    assert manifest_custom["batch_label"] == "sweep_001"


def test_artifact_bundle_writer_creates_expected_files(tmp_path):
    r1 = make_dummy_result("case-1", 0.5)
    
    output_dir = tmp_path / "artifacts"
    written_paths = write_artifact_bundle([r1], str(output_dir), batch_label="test_batch")
    
    # Verify the returned dictionary
    assert "summary_csv" in written_paths
    assert "summary_json" in written_paths
    assert "manifest_json" in written_paths
    
    # Verify actual files on disk
    assert Path(written_paths["summary_csv"]).name == "summary.csv"
    assert Path(written_paths["summary_json"]).name == "summary.json"
    assert Path(written_paths["manifest_json"]).name == "manifest.json"
    
    assert Path(written_paths["summary_csv"]).exists()
    assert Path(written_paths["summary_json"]).exists()
    assert Path(written_paths["manifest_json"]).exists()
    
    # Validate manifest content on disk
    manifest_content = json.loads(Path(written_paths["manifest_json"]).read_text(encoding="utf-8"))
    assert manifest_content["batch_label"] == "test_batch"


def test_artifact_bundle_works_with_real_harness_results(tmp_path):
    cases = [
        ExperimentCase(
            case_name="integration-case", 
            scenario_name="default_multihop", 
            tick_size=1, 
            simulation_end_override=5
        )
    ]
    
    # Generate real results from the simulator harness
    results = ExperimentHarness.run_experiments(cases)
    assert len(results) == 1
    
    output_dir = tmp_path / "real_artifacts"
    written_paths = write_artifact_bundle(results, str(output_dir))
    
    # Ensure they serialize properly
    manifest_content = json.loads(Path(written_paths["manifest_json"]).read_text(encoding="utf-8"))
    
    assert manifest_content["total_cases"] == 1
    assert manifest_content["case_names"] == ["integration-case"]
    
    csv_content = Path(written_paths["summary_csv"]).read_text(encoding="utf-8")
    assert "integration-case" in csv_content