import json
import copy
import pytest
from pathlib import Path

from sim.artifact_export import export_experiment_artifacts


@pytest.fixture
def mock_batch_result() -> dict:
    """Provides a minimal valid batch result mocking Wave-34 output."""
    return {
        "experiment_names": ["exp_A", "exp_B"],
        "results": [
            {"experiment_name": "exp_A", "status": "done"},
            {"experiment_name": "exp_B", "status": "done"}
        ],
        "aggregate_comparison": {
            "scenario_names": ["scenario_1", "scenario_2"],
            "per_scenario_summaries": [
                {
                    "scenario_name": "scenario_1",
                    "outcome": "successful_delivery",
                    "delivered_bundle_count": 10,
                    "fragments_delivered_total": 5
                },
                {
                    "scenario_name": "scenario_2",
                    "outcome": "expiry_observed",
                    "delivered_bundle_count": 2,
                    "fragments_delivered_total": 1
                }
            ],
            "aggregate": {}
        }
    }


def test_invalid_non_dict_batch_result_raises(tmp_path):
    with pytest.raises(ValueError, match="must be a dictionary"):
        export_experiment_artifacts(["not", "a", "dict"], tmp_path)


def test_missing_required_keys_raise(tmp_path):
    invalid_batch = {"experiment_names": []} # Missing 'results' and 'aggregate_comparison'
    with pytest.raises(ValueError, match="missing required key: 'results'"):
        export_experiment_artifacts(invalid_batch, tmp_path)


def test_export_creates_output_dir_and_writes_expected_files(mock_batch_result, tmp_path):
    # Use a nested path to ensure mkdir(parents=True) works
    out_dir = tmp_path / "deep" / "nested" / "artifacts"
    
    export_experiment_artifacts(mock_batch_result, out_dir)
    
    assert out_dir.exists()
    assert (out_dir / "batch_result.json").exists()
    assert (out_dir / "aggregate_comparison.json").exists()
    assert (out_dir / "visualization_spec.json").exists()
    assert (out_dir / "manifest.json").exists()


def test_returned_file_mapping_contains_expected_keys_and_paths(mock_batch_result, tmp_path):
    mapping = export_experiment_artifacts(mock_batch_result, tmp_path)
    
    expected_keys = ["batch_result", "aggregate_comparison", "visualization_spec", "manifest"]
    for key in expected_keys:
        assert key in mapping
        # Ensure the returned path string points to an actual file
        assert Path(mapping[key]).exists()


def test_manifest_contains_correct_metadata(mock_batch_result, tmp_path):
    mapping = export_experiment_artifacts(mock_batch_result, tmp_path)
    
    manifest_path = Path(mapping["manifest"])
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    assert manifest_data["source"] == "AetherNet Wave-36 artifact export"
    assert manifest_data["experiment_count"] == 2
    assert manifest_data["experiment_names"] == ["exp_A", "exp_B"]
    assert "exported_files" in manifest_data
    assert manifest_data["exported_files"]["batch_result"] == "batch_result.json"


def test_visualization_spec_file_written_and_contains_charts(mock_batch_result, tmp_path):
    mapping = export_experiment_artifacts(mock_batch_result, tmp_path)
    
    vis_path = Path(mapping["visualization_spec"])
    with vis_path.open("r", encoding="utf-8") as f:
        vis_data = json.load(f)
        
    assert "charts" in vis_data
    assert "delivery_by_scenario" in vis_data["charts"]
    assert vis_data["charts"]["delivery_by_scenario"]["x"] == ["scenario_1", "scenario_2"]
    assert vis_data["charts"]["delivery_by_scenario"]["y"] == [10, 2]


def test_export_does_not_mutate_input_batch_result(mock_batch_result, tmp_path):
    original_copy = copy.deepcopy(mock_batch_result)
    
    export_experiment_artifacts(mock_batch_result, tmp_path)
    
    # Assert the dictionary was not modified in-place
    assert mock_batch_result == original_copy