from dataclasses import dataclass
from typing import Any, Dict, List

VALID_STATUSES = {"info", "success", "warning", "error"}


@dataclass(frozen=True)
class RoutingInsightConclusion:
    text: str
    status: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("conclusion text must be non-empty")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported status: {self.status}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "text": self.text,
            "status": self.status,
        }


@dataclass(frozen=True)
class RoutingInsight:
    scenario_id: str
    observations: List[str]
    conclusions: List[RoutingInsightConclusion]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")

        object.__setattr__(self, "observations", list(self.observations))
        object.__setattr__(self, "conclusions", list(self.conclusions))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "observations": list(self.observations),
            "conclusions": [conclusion.to_dict() for conclusion in self.conclusions],
        }


class RoutingInsightGenerator:
    """
    Deterministic insight generator based purely on observable routing differences.

    Semantic status is assigned here so UI/export layers do not parse strings.
    """

    def generate(self, scenario_data: Dict[str, Any]) -> RoutingInsight:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {
            result["routing_mode"]: result["selected_next_hop"]
            for result in results
        }

        legacy = result_map.get("legacy")
        balanced = result_map.get("phase6_balanced")
        adaptive = result_map.get("phase6_adaptive")

        observations: List[str] = []
        conclusions: List[RoutingInsightConclusion] = []

        if legacy == balanced == adaptive:
            observations.append(f"All routing modes selected the same next hop: {legacy}.")
            conclusions.append(
                RoutingInsightConclusion(
                    text="No routing divergence observed under this scenario.",
                    status="info",
                )
            )
            return RoutingInsight(scenario_id, observations, conclusions)

        if legacy != balanced:
            observations.append(
                f"Routing divergence detected: legacy={legacy}, "
                f"balanced={balanced}, adaptive={adaptive}."
            )
            observations.append(
                f"Phase-6 changed routing decision from {legacy} to {balanced}."
            )
            conclusions.append(
                RoutingInsightConclusion(
                    text=(
                        "Phase-6 applies additional filtering or prioritization "
                        "beyond legacy scoring."
                    ),
                    status="success",
                )
            )

        if balanced is None and adaptive is None:
            conclusions.append(
                RoutingInsightConclusion(
                    text="Phase-6 filtered all candidates under strict safety constraints.",
                    status="warning",
                )
            )

        if adaptive != balanced:
            observations.append(
                f"Adaptive mode differs from balanced: adaptive={adaptive}, balanced={balanced}."
            )
            conclusions.append(
                RoutingInsightConclusion(
                    text="Adaptive mode preserves alternative routing behavior.",
                    status="info",
                )
            )

        if not observations:
            observations.append("No significant routing pattern detected.")
            conclusions.append(
                RoutingInsightConclusion(
                    text="No strong routing conclusion was produced.",
                    status="info",
                )
            )

        return RoutingInsight(scenario_id, observations, conclusions)