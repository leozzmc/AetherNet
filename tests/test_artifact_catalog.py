import json
from pathlib import Path
import pytest

from sim.experiment_harness import ExperimentCase, ExperimentHarness
from sim.experiment_artifacts import write_artifact_bundle
from sim.artifact_catalog import (
    read_artifact_bundle,
    build_artifact_catalog,
    catalog_to_json,
    write_artifact_catalog,
)


def create_dummy_bundle(base_path: Path, bundle_name: str, valid: bool = True):
    bundle_dir = base_path / bundle_name
    bundle_dir.mkdir(parents=True)
    
    if valid:
        (bundle_dir / "summary.csv").write_text("dummy,csv", encoding="utf-8")
        (bundle_dir / "summary.json").write_text('{"dummy": "json"}', encoding="utf-8")
        
        manifest = {
            "artifact_version": "1.0",
            "batch_label": f"label_{bundle_name}",
            "total_cases": 2,
            "case_names": ["case1", "case2"],
            "generated_files": ["summary.csv", "summary.json", "manifest.json"],
            "column_order": []
        }
        (bundle_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    else:
        # Invalid bundle: missing summary.csv
        (bundle_dir / "summary.json").write_text('{"dummy": "json"}', encoding="utf-8")
        (bundle_dir / "manifest.json").write_text('{"dummy": "json"}', encoding="utf-8")
        
    return bundle_dir


def test_single_bundle_reader_validates_required_files(tmp_path):
    valid_dir = create_dummy_bundle(tmp_path, "valid_bundle", valid=True)
    
    manifest = read_artifact_bundle(str(valid_dir))
    assert manifest["batch_label"] == "label_valid_bundle"
    assert manifest["path"] == str(valid_dir.resolve())


def test_invalid_bundle_raises_clearly(tmp_path):
    invalid_dir = create_dummy_bundle(tmp_path, "invalid_bundle", valid=False)
    
    with pytest.raises(ValueError) as excinfo:
        read_artifact_bundle(str(invalid_dir))
        
    assert "Missing required file" in str(excinfo.value)
    assert "summary.csv" in str(excinfo.value)


def test_catalog_builder_preserves_deterministic_batch_order(tmp_path):
    # Create in random order
    create_dummy_bundle(tmp_path, "batch_Z")
    create_dummy_bundle(tmp_path, "batch_A")
    create_dummy_bundle(tmp_path, "batch_M")
    
    catalog = build_artifact_catalog(str(tmp_path))
    
    assert catalog["total_batches"] == 3
    # Should be strictly sorted: A, M, Z
    assert catalog["batches"][0]["directory_name"] == "batch_A"
    assert catalog["batches"][1]["directory_name"] == "batch_M"
    assert catalog["batches"][2]["directory_name"] == "batch_Z"


def test_catalog_json_output_is_deterministic(tmp_path):
    create_dummy_bundle(tmp_path, "batch_1")
    catalog = build_artifact_catalog(str(tmp_path))
    
    json_1 = catalog_to_json(catalog)
    json_2 = catalog_to_json(catalog)
    
    assert json_1 == json_2
    assert "batch_1" in json_1
    assert "label_batch_1" in json_1


def test_catalog_writer_writes_expected_file(tmp_path):
    create_dummy_bundle(tmp_path, "batch_1")
    
    output_file = tmp_path / "master_catalog.json"
    written_path = write_artifact_catalog(str(tmp_path), str(output_file))
    
    assert Path(written_path).exists()
    
    content = json.loads(Path(written_path).read_text(encoding="utf-8"))
    assert content["total_batches"] == 1
    assert content["batches"][0]["directory_name"] == "batch_1"


def test_catalog_works_with_real_wave55_artifact_bundles(tmp_path):
    cases = [
        ExperimentCase(
            case_name="integration-case-1", 
            scenario_name="default_multihop", 
            tick_size=1, 
            simulation_end_override=5
        )
    ]
    
    results = ExperimentHarness.run_experiments(cases)
    
    # Write a real bundle using Wave-55
    bundle_dir = tmp_path / "real_batch"
    write_artifact_bundle(results, str(bundle_dir), batch_label="real_integration_test")
    
    # Read it back using Wave-56 catalog
    catalog = build_artifact_catalog(str(tmp_path))
    
    assert catalog["total_batches"] == 1
    assert catalog["batches"][0]["batch_label"] == "real_integration_test"
    assert catalog["batches"][0]["total_cases"] == 1
    assert "integration-case-1" in catalog["batches"][0]["case_names"]