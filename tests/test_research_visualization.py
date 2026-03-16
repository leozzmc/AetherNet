import pytest
from sim.research_visualization import (
    build_visualization_spec,
    build_visualization_spec_from_experiment_batch
)


@pytest.fixture
def mock_comparison_report() -> dict:
    return {
        "scenario_names": ["scenario_A", "scenario_B"],
        "per_scenario_summaries": [
            {
                "scenario_name": "scenario_A",
                "outcome": "successful_delivery",
                "delivered_bundle_count": 10,
                "expired_total": 0,
                "remaining_store_count": 2,
                "fragments_delivered_total": 20,
                "fragments_expired_total": 0,
            },
            {
                "scenario_name": "scenario_B",
                "outcome": "expiry_observed",
                "delivered_bundle_count": 5,
                "expired_total": 3,
                "remaining_store_count": 8,
                "fragments_delivered_total": 12,
                "fragments_expired_total": 5,
            }
        ],
        "aggregate": {}
    }


def test_invalid_non_dict_input_raises():
    with pytest.raises(ValueError, match="must be a dictionary"):
        build_visualization_spec(["not", "a", "dict"])


def test_missing_per_scenario_summaries_raises():
    with pytest.raises(ValueError, match="must contain 'per_scenario_summaries'"):
        build_visualization_spec({"wrong_key": []})


def test_non_list_per_scenario_summaries_raises():
    with pytest.raises(ValueError, match="'per_scenario_summaries' must be a list"):
        build_visualization_spec({"per_scenario_summaries": "not_a_list"})


def test_visualization_spec_preserves_scenario_order(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    expected_order = ["scenario_A", "scenario_B"]
    
    assert spec["charts"]["delivery_by_scenario"]["x"] == expected_order
    assert spec["charts"]["expiry_by_scenario"]["x"] == expected_order


def test_delivery_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["delivery_by_scenario"]
    
    assert chart["type"] == "bar"
    assert chart["y"] == [10, 5]


def test_expiry_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["expiry_by_scenario"]
    
    assert chart["type"] == "bar"
    assert chart["y"] == [0, 3]


def test_remaining_store_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["remaining_store_by_scenario"]
    
    assert chart["type"] == "bar"
    assert chart["y"] == [2, 8]


def test_fragment_delivery_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["fragment_delivery_by_scenario"]
    
    assert chart["type"] == "bar"
    assert chart["y"] == [20, 12]


def test_fragment_expiry_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["fragment_expiry_by_scenario"]
    
    assert chart["type"] == "bar"
    assert chart["y"] == [0, 5]


def test_outcome_by_scenario_populated_correctly(mock_comparison_report):
    spec = build_visualization_spec(mock_comparison_report)
    chart = spec["charts"]["outcome_by_scenario"]
    
    assert chart["type"] == "categorical"
    assert len(chart["items"]) == 2
    assert chart["items"][0] == {"scenario_name": "scenario_A", "outcome": "successful_delivery"}
    assert chart["items"][1] == {"scenario_name": "scenario_B", "outcome": "expiry_observed"}


def test_build_from_experiment_batch_helper(mock_comparison_report):
    mock_batch = {
        "experiment_names": ["exp1", "exp2"],
        "aggregate_comparison": mock_comparison_report
    }
    
    spec = build_visualization_spec_from_experiment_batch(mock_batch)
    assert spec["meta"]["scenario_count"] == 2
    assert spec["charts"]["delivery_by_scenario"]["y"] == [10, 5]