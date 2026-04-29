import pytest

from aether_phase6_presentation.builder import (
    FlowEdge,
    FlowNode,
    PresentationBuilder,
)


@pytest.fixture
def mock_structured_report() -> dict:
    return {
        "suite_id": "test_suite",
        "summary": {
            "total_decisions": 3,
            "filtered_all_count": 0,
            "mode_counts": {
                "legacy": 1,
                "phase6_balanced": 1,
                "phase6_adaptive": 1,
            },
        },
        "scenarios": [
            {
                "scenario_id": "jammed",
                "results": [
                    {
                        "routing_mode": "legacy",
                        "selected_next_hop": "L2",
                        "decision_reason": "score",
                    },
                    {
                        "routing_mode": "phase6_balanced",
                        "selected_next_hop": "L1",
                        "decision_reason": "filtered",
                    },
                    {
                        "routing_mode": "phase6_adaptive",
                        "selected_next_hop": "L1",
                        "decision_reason": "filtered",
                    },
                ],
            }
        ],
    }


def test_presentation_builder_generates_correct_schema(mock_structured_report: dict) -> None:
    bundle = PresentationBuilder().build(mock_structured_report)

    assert len(bundle.scenarios) == 1

    scenario = bundle.scenarios[0]
    data = scenario.to_dict()

    assert scenario.scenario_id == "jammed"
    assert data["decisions"]["legacy"] == "L2"
    assert data["decisions"]["balanced"] == "L1"
    assert data["decisions"]["adaptive"] == "L1"

    assert len(data["nodes"]) > 0
    assert len(data["edges"]) == len(data["nodes"]) - 1

    first_node = data["nodes"][0]
    assert first_node["id"] == "step-0"
    assert "data" in first_node
    assert "label" in first_node["data"]
    assert "status" in first_node["data"]

    first_edge = data["edges"][0]
    assert first_edge["source"] == "step-0"
    assert first_edge["target"] == "step-1"


def test_presentation_bundle_is_deterministic(mock_structured_report: dict) -> None:
    builder = PresentationBuilder()

    first = builder.build(mock_structured_report).to_dict()
    second = builder.build(mock_structured_report).to_dict()

    assert first == second


def test_presentation_marks_divergence(mock_structured_report: dict) -> None:
    scenario = PresentationBuilder().build(mock_structured_report).scenarios[0]

    assert scenario.metrics["diverged"] is True
    assert any(edge.status == "success" for edge in scenario.edges)


def test_none_next_hop_is_rendered_as_NONE() -> None:
    report = {
        "summary": {},
        "scenarios": [
            {
                "scenario_id": "lockdown",
                "results": [
                    {"routing_mode": "legacy", "selected_next_hop": "L2"},
                    {"routing_mode": "phase6_balanced", "selected_next_hop": None},
                    {"routing_mode": "phase6_adaptive", "selected_next_hop": None},
                ],
            }
        ],
    }

    scenario = PresentationBuilder().build(report).scenarios[0]
    data = scenario.to_dict()

    assert data["decisions"]["balanced"] == "NONE"
    assert data["decisions"]["adaptive"] == "NONE"


def test_no_mutation_leakage(mock_structured_report: dict) -> None:
    scenario = PresentationBuilder().build(mock_structured_report).scenarios[0]

    data = scenario.to_dict()
    data["metrics"]["diverged"] = False
    data["nodes"][0]["data"]["label"] = "hacked"
    data["story"]["summary"] = "hacked"
    data["conclusions"][0]["text"] = "hacked"

    fresh = scenario.to_dict()

    assert fresh["metrics"]["diverged"] is True
    assert fresh["nodes"][0]["data"]["label"] != "hacked"
    assert fresh["story"]["summary"] != "hacked"
    assert fresh["conclusions"][0]["text"] != "hacked"


def test_flow_node_validation() -> None:
    with pytest.raises(ValueError, match="unsupported node type"):
        FlowNode("node-1", "Node", "bad-type", "info")

    with pytest.raises(ValueError, match="unsupported node status"):
        FlowNode("node-1", "Node", "input", "bad-status")


def test_flow_edge_validation() -> None:
    with pytest.raises(ValueError, match="unsupported edge status"):
        FlowEdge("edge-1", "source", "target", "bad-status")