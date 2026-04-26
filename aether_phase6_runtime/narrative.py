from dataclasses import dataclass
from typing import Any, Dict, List

from .insight import RoutingInsight


@dataclass(frozen=True)
class RoutingNarrative:
    scenario_id: str
    interview: str
    demo: str
    summary: str


class RoutingNarrativeGenerator:
    """
    Converts routing behavior into system-aware, concrete narratives.
    """

    def generate(self, scenario_data: Dict[str, Any], insight: RoutingInsight) -> RoutingNarrative:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {
            r["routing_mode"]: r["selected_next_hop"]
            for r in results
        }

        legacy = result_map.get("legacy")
        balanced = result_map.get("phase6_balanced")
        adaptive = result_map.get("phase6_adaptive")

        # --- Case 1: No divergence ---
        if legacy == balanced == adaptive:
            interview = (
                f"In the {scenario_id} scenario, all routing modes converge to the same next hop ({legacy}). "
                "This indicates that no additional filtering or prioritization is triggered, "
                "and the routing decision is purely driven by baseline scoring."
            )

            demo = f"All modes select {legacy}, no difference observed."

            summary = "No routing divergence."

            return RoutingNarrative(scenario_id, interview, demo, summary)

        # --- Case 2: Legacy vs Phase-6 divergence ---
        interview_parts: List[str] = []
        demo_parts: List[str] = []
        summary_parts: List[str] = []

        if legacy != balanced:
            interview_parts.append(
                f"In the {scenario_id} scenario, legacy routing selects {legacy}, "
                f"while Phase-6 balanced routing selects {balanced}. "
                "This demonstrates that Phase-6 applies additional filtering "
                "or prioritization beyond pure score-based selection."
            )

            demo_parts.append(
                f"Legacy picks {legacy}, Phase-6 reroutes to {balanced}."
            )

            summary_parts.append("Phase-6 modifies routing decision.")

        # --- Case 3: Adaptive divergence ---
        if adaptive != balanced:
            interview_parts.append(
                f"Adaptive mode further diverges by selecting {adaptive}, "
                "indicating alternative routing strategies beyond balanced mode."
            )

            demo_parts.append(
                f"Adaptive explores alternative path: {adaptive}."
            )

            summary_parts.append("Adaptive mode diverges.")

        # fallback safety
        if not interview_parts:
            interview_parts.append(
                "Routing behavior differs across modes, indicating internal decision variance."
            )
            demo_parts.append("Modes behave differently.")
            summary_parts.append("Routing divergence detected.")

        return RoutingNarrative(
            scenario_id=scenario_id,
            interview=" ".join(interview_parts),
            demo=" ".join(demo_parts),
            summary=" ".join(summary_parts),
        )