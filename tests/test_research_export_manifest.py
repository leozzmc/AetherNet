import json
from pathlib import Path
import pytest

from sim.baseline_profiles import build_baseline_profile
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.experiment_artifacts import write_artifact_bundle
from sim.sweep_aggregation import write_sweep_aggregation
from sim.research_table_export import export_research_tables
from sim.research_export_manifest import write_research_export_manifest


def create_mock_environment(tmp_path: Path, overrides: dict = None) -> tuple[Path, Path]:
    """Helper to mock Wave-63 and Wave-64 outputs for isolated testing."""
    agg_dir = tmp_path / "agg"
    agg_dir.mkdir(parents=True, exist_ok=True)
    
    agg_data = {
        "type": "sweep_aggregation",
        "version": "1.0",
        "root_path": "/mock/root",
        "artifact_count": 2,
        "case_count": 3,
        "cases": []
    }
    if overrides:
        agg_data.update(overrides)
        
    agg_json_path = agg_dir / "sweep_aggregation.json"
    agg_json_path.write_text(json.dumps(agg_data), encoding="utf-8")
    
    export_dir = tmp_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    (export_dir / "research_case_batch_table.csv").write_text("header1,header2\nr1,v1\nr2,v2\n", encoding="utf-8")
    (export_dir / "research_case_summary_table.csv").write_text("header1\nr1\n", encoding="utf-8")
    
    return agg_json_path, export_dir


def test_valid_manifest_export(tmp_path):
    agg_json, export_dir = create_mock_environment(tmp_path)
    
    manifest_path_str = write_research_export_manifest(str(agg_json), str(export_dir))
    manifest_path = Path(manifest_path_str)
    
    assert manifest_path.is_file()
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["type"] == "research_export_manifest"
    assert manifest["version"] == "1.0"
    
    # Lineage is preserved
    assert manifest["aggregation_source"]["artifact_count"] == 2
    assert manifest["aggregation_source"]["case_count"] == 3
    assert manifest["aggregation_source"]["path"] == str(agg_json.resolve())
    
    # Counts match the mocked CSVs
    assert manifest["table_row_counts"]["research_case_batch_table"] == 2
    assert manifest["table_row_counts"]["research_case_summary_table"] == 1


def test_missing_research_table_file_raises(tmp_path):
    agg_json, export_dir = create_mock_environment(tmp_path)
    
    # Delete one of the required CSVs
    (export_dir / "research_case_batch_table.csv").unlink()
    
    with pytest.raises(ValueError) as excinfo:
        write_research_export_manifest(str(agg_json), str(export_dir))
        
    assert "Required research table missing" in str(excinfo.value)


def test_invalid_aggregation_type_version_raises(tmp_path):
    agg_json1, export_dir1 = create_mock_environment(tmp_path / "test1", {"type": "wrong_type"})
    with pytest.raises(ValueError) as excinfo1:
        write_research_export_manifest(str(agg_json1), str(export_dir1))
    assert "type must be 'sweep_aggregation'" in str(excinfo1.value)

    agg_json2, export_dir2 = create_mock_environment(tmp_path / "test2", {"version": "9.9"})
    with pytest.raises(ValueError) as excinfo2:
        write_research_export_manifest(str(agg_json2), str(export_dir2))
    assert "version must be '1.0'" in str(excinfo2.value)


def test_row_counts_recorded_correctly_excluding_headers(tmp_path):
    agg_json, export_dir = create_mock_environment(tmp_path)
    
    # 1 header + 5 data rows
    (export_dir / "research_case_batch_table.csv").write_text("h\n1\n2\n3\n4\n5\n", encoding="utf-8")
    
    # 1 header + 0 data rows
    (export_dir / "research_case_summary_table.csv").write_text("h\n", encoding="utf-8")
    
    write_research_export_manifest(str(agg_json), str(export_dir))
    
    manifest = json.loads((export_dir / "research_export_manifest.json").read_text(encoding="utf-8"))
    
    assert manifest["table_row_counts"]["research_case_batch_table"] == 5
    assert manifest["table_row_counts"]["research_case_summary_table"] == 0


def test_deterministic_repeated_export(tmp_path):
    agg_json, export_dir = create_mock_environment(tmp_path)
    
    path_1 = write_research_export_manifest(str(agg_json), str(export_dir))
    path_2 = write_research_export_manifest(str(agg_json), str(export_dir))
    
    assert Path(path_1).read_text(encoding="utf-8") == Path(path_2).read_text(encoding="utf-8")


def test_integration_with_real_pipeline(tmp_path):
    """
    Wave-65: Full pipeline integration test. Ensure the manifest perfectly describes
    outputs generated from real simulation artifacts and table exports.
    """
    # 1. Profile & Sweep (Wave-61, Wave-62)
    sweep_cases = build_parameter_sweep(
        "minimal_baseline",
        {"tick_size": [1, 2]},
    )
    
    # 2. Run Harness (Wave-52)
    results = ExperimentHarness.run_experiments(sweep_cases)

    # 3. Write Artifact Bundles (Wave-55)
    artifacts_dir = tmp_path / "artifacts"
    write_artifact_bundle(results, str(artifacts_dir / "batch_1"), batch_label="run_1")
    write_artifact_bundle(results, str(artifacts_dir / "batch_2"), batch_label="run_2")

    # 4. Sweep Aggregation (Wave-63)
    agg_dir = tmp_path / "aggregation"
    write_sweep_aggregation(str(artifacts_dir), str(agg_dir))
    agg_json_path = agg_dir / "sweep_aggregation.json"

    # 5. Research Table Export (Wave-64)
    export_dir = tmp_path / "research_tables"
    export_research_tables(str(agg_json_path), str(export_dir))

    # 6. Research Export Manifest (Wave-65)
    manifest_path_str = write_research_export_manifest(str(agg_json_path), str(export_dir))
    manifest_path = Path(manifest_path_str)
    
    assert manifest_path.is_file()
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["type"] == "research_export_manifest"
    
    # Lineage matches the pipeline output
    assert manifest["aggregation_source"]["artifact_count"] == 2
    assert manifest["aggregation_source"]["case_count"] == 2
    
    # Sweep across 2 tick sizes -> 2 cases, each across 2 batches -> 4 batch rows, 2 summary rows
    assert manifest["table_row_counts"]["research_case_batch_table"] == 4
    assert manifest["table_row_counts"]["research_case_summary_table"] == 2