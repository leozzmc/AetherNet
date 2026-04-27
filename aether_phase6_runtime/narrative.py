from dataclasses import dataclass
from typing import Any, Dict, List

from .insight import RoutingInsight, VALID_STATUSES


@dataclass(frozen=True)
class RoutingNarrative:
    scenario_id: str
    interview: str
    demo: str
    summary: str
    demo_status: str
    summary_status: str

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if not self.interview.strip():
            raise ValueError("interview must be non-empty")
        if not self.demo.strip():
            raise ValueError("demo must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        if self.demo_status not in VALID_STATUSES:
            raise ValueError(f"unsupported demo_status: {self.demo_status}")
        if self.summary_status not in VALID_STATUSES:
            raise ValueError(f"unsupported summary_status: {self.summary_status}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "scenario_id": self.scenario_id,
            "interview": self.interview,
            "demo": self.demo,
            "summary": self.summary,
            "demo_status": self.demo_status,
            "summary_status": self.summary_status,
        }


class RoutingNarrativeGenerator:
    """
    Converts routing behavior into concrete narratives and explicit rendering status.
    """

    def generate(
        self,
        scenario_data: Dict[str, Any],
        insight: RoutingInsight,
    ) -> RoutingNarrative:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {
            result["routing_mode"]: result["selected_next_hop"]
            for result in results
        }

        legacy = result_map.get("legacy")
        balanced = result_map.get("phase6_balanced")
        adaptive = result_map.get("phase6_adaptive")

        if legacy == balanced == adaptive:
            return RoutingNarrative(
                scenario_id=scenario_id,
                interview=(
                    f"In the {scenario_id} scenario, all routing modes converge "
                    f"to the same next hop ({legacy}). This indicates that no additional "
                    "filtering or prioritization is triggered, and the routing decision "
                    "is driven by baseline scoring."
                ),
                demo=f"All modes select {legacy}, no difference observed.",
                summary="No routing divergence.",
                demo_status="info",
                summary_status="info",
            )

        interview_parts: List[str] = []
        demo_parts: List[str] = []
        summary_parts: List[str] = []

        demo_status = "info"
        summary_status = "info"

        if legacy != balanced:
            interview_parts.append(
                f"In the {scenario_id} scenario, legacy routing selects {legacy}, "
                f"while Phase-6 balanced routing selects {balanced}. This demonstrates "
                "that Phase-6 applies additional filtering or prioritization beyond "
                "pure score-based selection."
            )
            demo_parts.append(f"Legacy picks {legacy}, Phase-6 reroutes to {balanced}.")
            summary_parts.append("Phase-6 modifies routing decision.")
            demo_status = "success"
            summary_status = "success"

        if adaptive != balanced:
            interview_parts.append(
                f"Adaptive mode further diverges by selecting {adaptive}, indicating "
                "alternative routing behavior beyond balanced mode."
            )
            demo_parts.append(f"Adaptive explores alternative path: {adaptive}.")

            if not summary_parts:
                summary_parts.append("Adaptive mode diverges.")
                summary_status = "info"
            else:
                summary_parts.append("Adaptive mode also diverges.")

        if not interview_parts:
            interview_parts.append("Routing behavior differs across modes.")
            demo_parts.append("Modes behave differently.")
            summary_parts.append("Routing divergence detected.")

        return RoutingNarrative(
            scenario_id=scenario_id,
            interview=" ".join(interview_parts),
            demo=" ".join(demo_parts),
            summary=" ".join(summary_parts),
            demo_status=demo_status,
            summary_status=summary_status,
        )