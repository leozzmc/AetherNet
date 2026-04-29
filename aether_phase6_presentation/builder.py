from dataclasses import dataclass
from typing import Any, Dict, List

from aether_phase6_runtime.insight import RoutingInsightGenerator
from aether_phase6_runtime.narrative import RoutingNarrativeGenerator
from aether_phase6_runtime.trace import DecisionTraceBuilder


VALID_STATUSES = {"info", "success", "warning", "error"}
VALID_NODE_TYPES = {"input", "process", "decision", "output"}


@dataclass(frozen=True)
class FlowNode:
    id: str
    label: str
    type: str
    status: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("node id must be non-empty")
        if not self.label.strip():
            raise ValueError("node label must be non-empty")
        if self.type not in VALID_NODE_TYPES:
            raise ValueError(f"unsupported node type: {self.type}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported node status: {self.status}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "data": {
                "label": self.label,
                "status": self.status,
            },
            "presentation": {
                "label": self.label,
                "status": self.status,
            },
        }


@dataclass(frozen=True)
class FlowEdge:
    id: str
    source: str
    target: str
    status: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("edge id must be non-empty")
        if not self.source.strip():
            raise ValueError("edge source must be non-empty")
        if not self.target.strip():
            raise ValueError("edge target must be non-empty")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported edge status: {self.status}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "status": self.status,
        }


@dataclass(frozen=True)
class ScenarioPresentation:
    scenario_id: str
    metrics: Dict[str, Any]
    legacy: str
    balanced: str
    adaptive: str
    nodes: List[FlowNode]
    edges: List[FlowEdge]
    story: Dict[str, str]
    conclusions: List[Dict[str, str]]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")

        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(self, "nodes", list(self.nodes))
        object.__setattr__(self, "edges", list(self.edges))
        object.__setattr__(self, "story", dict(self.story))
        object.__setattr__(self, "conclusions", [dict(item) for item in self.conclusions])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "metrics": dict(self.metrics),
            "decisions": {
                "legacy": self.legacy,
                "balanced": self.balanced,
                "adaptive": self.adaptive,
            },
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "story": dict(self.story),
            "conclusions": [dict(item) for item in self.conclusions],
        }


@dataclass(frozen=True)
class PresentationBundle:
    scenarios: List[ScenarioPresentation]
    global_summary: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenarios", list(self.scenarios))
        object.__setattr__(self, "global_summary", dict(self.global_summary))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "presentation_bundle",
            "version": "1.0",
            "global_summary": dict(self.global_summary),
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }


class PresentationBuilder:
    """
    Maps Phase-6 backend artifacts into frontend-ready presentation data.

    The frontend should render this output directly and should not perform
    routing or security inference.
    """

    def __init__(self) -> None:
        self._insight_gen = RoutingInsightGenerator()
        self._narrative_gen = RoutingNarrativeGenerator()
        self._trace_gen = DecisionTraceBuilder()

    def build(self, structured_report: Dict[str, Any]) -> PresentationBundle:
        scenarios: List[ScenarioPresentation] = []

        for scenario_data in structured_report.get("scenarios", []):
            scenarios.append(self._build_scenario(scenario_data))

        return PresentationBundle(
            scenarios=scenarios,
            global_summary=structured_report.get("summary", {}),
        )

    def _build_scenario(self, scenario_data: Dict[str, Any]) -> ScenarioPresentation:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {
            result["routing_mode"]: result.get("selected_next_hop")
            for result in results
        }

        legacy = self._display_hop(result_map.get("legacy"))
        balanced = self._display_hop(result_map.get("phase6_balanced"))
        adaptive = self._display_hop(result_map.get("phase6_adaptive"))

        insight = self._insight_gen.generate(scenario_data)
        narrative = self._narrative_gen.generate(scenario_data, insight)
        trace = self._trace_gen.build(scenario_data)

        nodes = self._build_nodes(trace.steps)
        edges = self._build_edges(trace.steps)

        story = {
            "context": scenario_id,
            "demo": narrative.demo,
            "demo_status": narrative.demo_status,
            "summary": narrative.summary,
            "summary_status": narrative.summary_status,
            "technical_context": narrative.interview,
        }

        conclusions = [
            {
                "text": conclusion.text,
                "status": conclusion.status,
            }
            for conclusion in insight.conclusions
        ]

        metrics = {
            "evaluated_modes": len(results),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "diverged": legacy != balanced,
        }

        return ScenarioPresentation(
            scenario_id=scenario_id,
            metrics=metrics,
            legacy=legacy,
            balanced=balanced,
            adaptive=adaptive,
            nodes=nodes,
            edges=edges,
            story=story,
            conclusions=conclusions,
        )

    @staticmethod
    def _build_nodes(steps: List[Any]) -> List[FlowNode]:
        nodes: List[FlowNode] = []

        for index, step in enumerate(steps):
            if index == 0:
                node_type = "input"
            elif index == len(steps) - 1:
                node_type = "output"
            else:
                node_type = "process"

            nodes.append(
                FlowNode(
                    id=f"step-{index}",
                    label=step.text,
                    type=node_type,
                    status=step.status,
                )
            )

        return nodes

    @staticmethod
    def _build_edges(steps: List[Any]) -> List[FlowEdge]:
        edges: List[FlowEdge] = []

        for index in range(1, len(steps)):
            source = f"step-{index - 1}"
            target = f"step-{index}"

            edges.append(
                FlowEdge(
                    id=f"{source}-{target}",
                    source=source,
                    target=target,
                    status=steps[index].status,
                )
            )

        return edges

    @staticmethod
    def _display_hop(value: Any) -> str:
        return str(value) if value is not None else "NONE"