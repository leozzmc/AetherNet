import pytest

from aether_phase6_runtime.insight import (
    RoutingInsightConclusion,
    RoutingInsightGenerator,
)
from aether_phase6_runtime.narrative import (
    RoutingNarrative,
    RoutingNarrativeGenerator,
)


def test_invalid_insight_status_raises_error() -> None:
    with pytest.raises(ValueError, match="unsupported status"):
        RoutingInsightConclusion("Some text", "invalid_status")


def test_blank_insight_text_raises_error() -> None:
    with pytest.raises(ValueError, match="conclusion text must be non-empty"):
        RoutingInsightConclusion("   ", "info")


def test_no_divergence_returns_info_status() -> None:
    scenario_data = {
        "scenario_id": "clean",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L2"},
        ],
    }

    insight = RoutingInsightGenerator().generate(scenario_data)

    assert insight.conclusions[0].status == "info"
    assert insight.conclusions[0].text == "No routing divergence observed under this scenario."

    narrative = RoutingNarrativeGenerator().generate(scenario_data, insight)

    assert narrative.demo_status == "info"
    assert narrative.summary_status == "info"


def test_legacy_divergence_returns_success_status() -> None:
    scenario_data = {
        "scenario_id": "jammed",
        "results": [
            {"routing_mode": "legacy", "selected_next_hop": "L2"},
            {"routing_mode": "phase6_balanced", "selected_next_hop": "L1"},
            {"routing_mode": "phase6_adaptive", "selected_next_hop": "L1"},
        ],
    }

    insight = RoutingInsightGenerator().generate(scenario_data)

    assert any(conclusion.status == "success" for conclusion in insight.conclusions)

    narrative = RoutingNarrativeGenerator().generate(scenario_data, insight)

    assert narrative.demo_status == "success"
    assert narrative.summary_status == "success"


def test_invalid_narrative_status_raises_error() -> None:
    with pytest.raises(ValueError, match="unsupported demo_status"):
        RoutingNarrative(
            scenario_id="test",
            interview="interview",
            demo="demo",
            summary="summary",
            demo_status="bad",
            summary_status="info",
        )