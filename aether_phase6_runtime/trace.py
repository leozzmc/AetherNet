from dataclasses import dataclass
from typing import Any, Dict, List

VALID_TRACE_STATUSES = {"info", "success", "warning", "error"}


@dataclass(frozen=True)
class TraceStep:
    """
    A deterministic, UI-renderable step in the routing decision process.

    The status is explicit backend-provided semantic state.
    UI layers should render this status directly and should not infer severity
    from the step text.
    """

    text: str
    status: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("trace step text must be non-empty")
        if self.status not in VALID_TRACE_STATUSES:
            raise ValueError(f"unsupported status: {self.status}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "text": self.text,
            "status": self.status,
        }


@dataclass(frozen=True)
class RoutingDecisionTrace:
    """
    Deterministic step-by-step trace for one benchmark scenario.
    """

    scenario_id: str
    steps: List[TraceStep]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")

        object.__setattr__(self, "steps", list(self.steps))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "steps": [step.to_dict() for step in self.steps],
        }


class DecisionTraceBuilder:
    """
    Builds a deterministic routing decision trace from scenario result data.

    Important boundary:
    - This class does not import benchmark presets.
    - This class does not reconstruct topology from global state.
    - It only explains the observed scenario result artifact it receives.
    """

    def build(self, scenario_data: Dict[str, Any]) -> RoutingDecisionTrace:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {
            result["routing_mode"]: result.get("selected_next_hop")
            for result in results
        }

        legacy = result_map.get("legacy")
        balanced = result_map.get("phase6_balanced")
        adaptive = result_map.get("phase6_adaptive")

        candidate_hops = self._candidate_hops_from_results(results)

        steps: List[TraceStep] = [
            TraceStep(
                text=f"Scenario artifact loaded: {scenario_id}.",
                status="info",
            ),
            TraceStep(
                text=f"Observed next-hop candidates from evaluated modes: {candidate_hops}.",
                status="info",
            ),
            TraceStep(
                text=f"Legacy baseline selected next hop: {self._display_hop(legacy)}.",
                status="info",
            ),
        ]

        if legacy == balanced:
            steps.append(
                TraceStep(
                    text=(
                        "Phase-6 balanced mode agrees with legacy baseline: "
                        f"{self._display_hop(balanced)}."
                    ),
                    status="info",
                )
            )
        else:
            steps.append(
                TraceStep(
                    text=(
                        "Phase-6 balanced mode changed the routing decision: "
                        f"{self._display_hop(legacy)} -> {self._display_hop(balanced)}."
                    ),
                    status="success",
                )
            )

        if adaptive != balanced:
            steps.append(
                TraceStep(
                    text=(
                        "Adaptive mode produced a different decision from balanced mode: "
                        f"{self._display_hop(balanced)} -> {self._display_hop(adaptive)}."
                    ),
                    status="info",
                )
            )

        if balanced is None and adaptive is None:
            steps.append(
                TraceStep(
                    text="Phase-6 modes produced no available next hop.",
                    status="warning",
                )
            )
        else:
            steps.append(
                TraceStep(
                    text=f"Final Phase-6 balanced next hop: {self._display_hop(balanced)}.",
                    status="success" if legacy != balanced else "info",
                )
            )

        return RoutingDecisionTrace(
            scenario_id=scenario_id,
            steps=steps,
        )

    @staticmethod
    def _candidate_hops_from_results(results: List[Dict[str, Any]]) -> str:
        hops = []
        for result in results:
            hop = result.get("selected_next_hop")
            if hop is not None and hop not in hops:
                hops.append(hop)

        if not hops:
            return "NONE"

        return ", ".join(hops)

    @staticmethod
    def _display_hop(hop: Any) -> str:
        return str(hop) if hop is not None else "NONE"