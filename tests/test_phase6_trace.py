import pytest

from aether_phase6_runtime.trace import (
    DecisionTraceBuilder,
    TraceStep,
)


def test_trace_builder_clean_scenario() -> None:
    scenario_data = {
        "scenario_id": "clean",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L2"},
        ],
    }

    trace = DecisionTraceBuilder().build(scenario_data)

    assert trace.scenario_id == "clean"
    assert trace.steps[0].text == "Scenario artifact loaded: clean."
    assert "Observed next-hop candidates" in trace.steps[1].text
    assert "Legacy baseline selected next hop: L2." in trace.steps[2].text
    assert "agrees with legacy baseline: L2" in trace.steps[3].text
    assert "Final Phase-6 balanced next hop: L2." in trace.steps[-1].text
    assert trace.steps[-1].status == "info"


def test_trace_builder_divergence_scenario() -> None:
    scenario_data = {
        "scenario_id": "jammed",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L1"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L1"},
        ],
    }

    trace = DecisionTraceBuilder().build(scenario_data)

    assert trace.scenario_id == "jammed"
    assert any(
        "Phase-6 balanced mode changed the routing decision: L2 -> L1."
        == step.text
        for step in trace.steps
    )
    assert any(step.status == "success" for step in trace.steps)
    assert trace.steps[-1].text == "Final Phase-6 balanced next hop: L1."
    assert trace.steps[-1].status == "success"


def test_trace_builder_adaptive_divergence() -> None:
    scenario_data = {
        "scenario_id": "adaptive_case",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L3"},
        ],
    }

    trace = DecisionTraceBuilder().build(scenario_data)

    assert any(
        "Adaptive mode produced a different decision from balanced mode: L2 -> L3."
        == step.text
        for step in trace.steps
    )


def test_trace_builder_filtered_all_candidates() -> None:
    scenario_data = {
        "scenario_id": "lockdown_case",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": None},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": None},
        ],
    }

    trace = DecisionTraceBuilder().build(scenario_data)

    assert any(
        step.text == "Phase-6 modes produced no available next hop."
        and step.status == "warning"
        for step in trace.steps
    )


def test_trace_is_deterministic() -> None:
    scenario_data = {
        "scenario_id": "jammed",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L1"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L1"},
        ],
    }

    trace_1 = DecisionTraceBuilder().build(scenario_data)
    trace_2 = DecisionTraceBuilder().build(scenario_data)

    assert trace_1.to_dict() == trace_2.to_dict()


def test_invalid_trace_step_status_raises_error() -> None:
    with pytest.raises(ValueError, match="unsupported status"):
        TraceStep("Test", "invalid")


def test_blank_trace_step_text_raises_error() -> None:
    with pytest.raises(ValueError, match="trace step text must be non-empty"):
        TraceStep("   ", "info")