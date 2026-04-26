from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class RoutingInsight:
    scenario_id: str
    observations: List[str]
    conclusions: List[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", list(self.observations))
        object.__setattr__(self, "conclusions", list(self.conclusions))


class RoutingInsightGenerator:
    """
    Deterministic insight generator based purely on observable routing differences.
    """

    def generate(self, scenario_data: Dict[str, Any]) -> RoutingInsight:
        scenario_id = scenario_data["scenario_id"]
        results = scenario_data.get("results", [])

        # extract mode outputs
        result_map = {
            r["routing_mode"]: r["selected_next_hop"]
            for r in results
        }

        legacy = result_map.get("legacy")
        balanced = result_map.get("phase6_balanced")
        adaptive = result_map.get("phase6_adaptive")

        observations: List[str] = []
        conclusions: List[str] = []

        # --- 1. identical behavior ---
        hops = {h for h in result_map.values() if h is not None}

        if len(hops) == 1:
            observations.append(f"All routing modes selected the same next hop: {legacy}.")
            conclusions.append("No routing divergence observed under this scenario.")
            return RoutingInsight(scenario_id, observations, conclusions)

        # --- 2. divergence ---
        if legacy != balanced or legacy != adaptive:
            observations.append(
                f"Routing divergence detected: legacy={legacy}, balanced={balanced}, adaptive={adaptive}."
            )

        # --- 3. filtering behavior ---
        if balanced is None and adaptive is None:
            observations.append("Phase-6 filtered all candidates.")
            conclusions.append("Phase-6 may enforce strict safety constraints under this condition.")

        # --- 4. avoidance pattern ---
        if legacy is not None and balanced is not None:
            if legacy != balanced:
                observations.append(
                    f"Phase-6 changed routing decision from {legacy} to {balanced}."
                )
                conclusions.append(
                    "Phase-6 applies additional filtering or prioritization beyond legacy scoring."
                )

        # --- 5. adaptive vs balanced ---
        if adaptive is not None and balanced is not None:
            if adaptive != balanced:
                observations.append(
                    f"Adaptive mode differs from balanced: adaptive={adaptive}, balanced={balanced}."
                )
                conclusions.append(
                    "Adaptive mode preserves alternative routing choices."
                )

        # fallback
        if not observations:
            observations.append("No significant routing pattern detected.")

        return RoutingInsight(scenario_id, observations, conclusions)