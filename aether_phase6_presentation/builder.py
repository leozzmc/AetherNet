from dataclasses import dataclass
from typing import Any, Dict, List

from aether_phase6_runtime.insight import RoutingInsightGenerator
from aether_phase6_runtime.narrative import RoutingNarrativeGenerator
from aether_phase6_runtime.trace import DecisionTraceBuilder


VALID_STATUSES = {"info", "success", "warning", "error"}
VALID_NODE_KINDS = {"input", "process", "decision", "output"}


@dataclass(frozen=True)
class FlowNode:
    id: str
    label: str
    kind: str
    status: str
    x: int = 0
    y: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("node id must be non-empty")
        if not self.label.strip():
            raise ValueError("node label must be non-empty")
        if self.kind not in VALID_NODE_KINDS:
            raise ValueError(f"unsupported node type: {self.kind}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported node status: {self.status}")

    def _react_flow_type(self) -> str:
        if self.kind == "input":
            return "input"
        if self.kind == "output":
            return "output"
        return "default"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self._react_flow_type(),
            "position": {
                "x": self.x,
                "y": self.y,
            },
            "data": {
                "label": self.label,
                "status": self.status,
                "kind": self.kind,
            },
            # Backward-compatible presentation payload for older frontend mapper/tests.
            "presentation": {
                "label": self.label,
                "status": self.status,
                "kind": self.kind,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "status": self.status,
            "data": {
                "status": self.status,
            },
            # Backward-compatible presentation payload.
            "presentation": {
                "status": self.status,
            },
        }


@dataclass(frozen=True)
class StoryStep:
    id: str
    label: str
    message: str
    status: str
    highlight_nodes: List[str]
    highlight_edges: List[str]
    focus_node: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("story step id must be non-empty")
        if not self.label.strip():
            raise ValueError("story step label must be non-empty")
        if not self.message.strip():
            raise ValueError("story step message must be non-empty")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported story step status: {self.status}")

        object.__setattr__(self, "highlight_nodes", list(self.highlight_nodes))
        object.__setattr__(self, "highlight_edges", list(self.highlight_edges))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "message": self.message,
            "status": self.status,
            "highlight_nodes": list(self.highlight_nodes),
            "highlight_edges": list(self.highlight_edges),
            "focus_node": self.focus_node,
            # Reserved for future dual-path highlighting.
            "legacy_path": [],
            "phase6_path": [],
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
    story_script: List[StoryStep]
    story: Dict[str, str]
    conclusions: List[Dict[str, str]]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")

        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(self, "nodes", list(self.nodes))
        object.__setattr__(self, "edges", list(self.edges))
        object.__setattr__(self, "story_script", list(self.story_script))
        object.__setattr__(self, "story", dict(self.story))
        object.__setattr__(
            self,
            "conclusions",
            [dict(conclusion) for conclusion in self.conclusions],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "metrics": dict(self.metrics),
            "decisions": {
                # Legacy keys expected by older tests/tools.
                "legacy": self.legacy,
                "balanced": self.balanced,
                "adaptive": self.adaptive,
                # Explicit product-facing keys used by the current React UI.
                "phase6_balanced": self.balanced,
                "phase6_adaptive": self.adaptive,
            },
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "story_script": [step.to_dict() for step in self.story_script],
            "story": dict(self.story),
            "conclusions": [dict(conclusion) for conclusion in self.conclusions],
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
            "version": "1.1",
            "global_summary": dict(self.global_summary),
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }


class PresentationBuilder:
    """
    Maps Phase-6 backend artifacts into frontend-ready presentation data.

    Contract:
    - deterministic output
    - no routing inference in frontend
    - stable generic node IDs within each scenario: step-0, step-1, ...
    """

    def __init__(self) -> None:
        self._insight_gen = RoutingInsightGenerator()
        self._narrative_gen = RoutingNarrativeGenerator()
        self._trace_gen = DecisionTraceBuilder()

    def build(self, structured_report: Dict[str, Any]) -> PresentationBundle:
        scenarios = [
            self._build_scenario(scenario_data)
            for scenario_data in structured_report.get("scenarios", [])
        ]

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
        story_script = self._build_story_script(nodes, edges, trace.steps)

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
            # Product-facing keys used by current UI.
            "nodes": len(nodes),
            "edges": len(edges),
            "modes": len(results),
            "diverged": legacy != balanced,
            # Backward-compatible keys used by older tests/tools.
            "node_count": len(nodes),
            "edge_count": len(edges),
            "evaluated_modes": len(results),
        }

        return ScenarioPresentation(
            scenario_id=scenario_id,
            metrics=metrics,
            legacy=legacy,
            balanced=balanced,
            adaptive=adaptive,
            nodes=nodes,
            edges=edges,
            story_script=story_script,
            story=story,
            conclusions=conclusions,
        )

    @staticmethod
    def _node_id(index: int) -> str:
        return f"step-{index}"

    @staticmethod
    def _edge_id(source_index: int, target_index: int) -> str:
        return f"step-{source_index}-to-step-{target_index}"

    def _build_nodes(self, steps: List[Any]) -> List[FlowNode]:
        nodes: List[FlowNode] = []

        for index, step in enumerate(steps):
            if index == 0:
                kind = "input"
            elif index == len(steps) - 1:
                kind = "output"
            else:
                kind = "process"

            nodes.append(
                FlowNode(
                    id=self._node_id(index),
                    label=step.text,
                    kind=kind,
                    status=step.status,
                    x=index * 320,
                    y=0,
                )
            )

        return nodes

    def _build_edges(self, steps: List[Any]) -> List[FlowEdge]:
        edges: List[FlowEdge] = []

        for index in range(1, len(steps)):
            source_index = index - 1
            target_index = index

            edges.append(
                FlowEdge(
                    id=self._edge_id(source_index, target_index),
                    source=self._node_id(source_index),
                    target=self._node_id(target_index),
                    status=steps[index].status,
                )
            )

        return edges

    def _build_story_script(
        self,
        nodes: List[FlowNode],
        edges: List[FlowEdge],
        steps: List[Any],
    ) -> List[StoryStep]:
        if not nodes:
            return []

        script: List[StoryStep] = [
            StoryStep(
                id="frame-0",
                label="Initialization",
                message="Establishing telemetry...",
                status="info",
                highlight_nodes=[nodes[0].id],
                highlight_edges=[],
                focus_node=nodes[0].id,
            )
        ]

        active_nodes = [nodes[0].id]
        active_edges: List[str] = []

        for index in range(1, len(nodes)):
            active_nodes.append(nodes[index].id)
            active_edges.append(edges[index - 1].id)

            step_status = steps[index].status

            script.append(
                StoryStep(
                    id=f"frame-{index}",
                    label=f"Phase {index}: {step_status.capitalize()}",
                    message=steps[index].text,
                    status=step_status,
                    highlight_nodes=list(active_nodes),
                    highlight_edges=list(active_edges),
                    focus_node=nodes[index].id,
                )
            )

        return script

    @staticmethod
    def _display_hop(value: Any) -> str:
        return str(value) if value is not None else "NONE"