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
    x: int
    y: int

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
            "position": {"x": self.x, "y": self.y},
            "data": {
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "data": {"status": self.status},
        }


# --- NEW: Wave-111 Story Animation Script ---
@dataclass(frozen=True)
class StoryStep:
    id: str
    label: str
    message: str
    highlight_nodes: List[str]
    highlight_edges: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "message": self.message,
            "highlight_nodes": list(self.highlight_nodes),
            "highlight_edges": list(self.highlight_edges),
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
    story_script: List[StoryStep]  # Changed for Wave-111
    story: Dict[str, str]
    conclusions: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "metrics": dict(self.metrics),
            "decisions": {
                "legacy": self.legacy,
                "phase6_balanced": self.balanced,
                "phase6_adaptive": self.adaptive,
            },
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "story_script": [step.to_dict() for step in self.story_script],
            "story": dict(self.story),
            "conclusions": [dict(c) for c in self.conclusions],
        }


@dataclass(frozen=True)
class PresentationBundle:
    scenarios: List[ScenarioPresentation]
    global_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "presentation_bundle",
            "version": "1.1",
            "global_summary": dict(self.global_summary),
            "scenarios": [s.to_dict() for s in self.scenarios],
        }


class PresentationBuilder:
    def __init__(self) -> None:
        self._insight_gen = RoutingInsightGenerator()
        self._narrative_gen = RoutingNarrativeGenerator()
        self._trace_gen = DecisionTraceBuilder()

    def build(self, structured_report: Dict[str, Any]) -> PresentationBundle:
        scenarios = [
            self._build_scenario(scenario_data)
            for scenario_data in structured_report.get("scenarios", [])
        ]
        return PresentationBundle(scenarios, structured_report.get("summary", {}))

    def _build_scenario(self, scenario_data: Dict[str, Any]) -> ScenarioPresentation:
        scenario_id = scenario_data.get("scenario_id", "unknown")
        results = scenario_data.get("results", [])

        result_map = {r["routing_mode"]: r.get("selected_next_hop") for r in results}
        legacy = self._display_hop(result_map.get("legacy"))
        balanced = self._display_hop(result_map.get("phase6_balanced"))
        adaptive = self._display_hop(result_map.get("phase6_adaptive"))

        insight = self._insight_gen.generate(scenario_data)
        narrative = self._narrative_gen.generate(scenario_data, insight)
        trace = self._trace_gen.build(scenario_data)

        nodes = self._build_nodes(scenario_id, trace.steps)
        edges = self._build_edges(scenario_id, trace.steps)
        story_script = self._build_story_script(nodes, edges, trace.steps)

        story = {
            "context": scenario_id,
            "demo": narrative.demo,
            "demo_status": narrative.demo_status,
            "summary": narrative.summary,
            "summary_status": narrative.summary_status,
            "technical_context": narrative.interview,
        }

        conclusions = [{"text": c.text, "status": c.status} for c in insight.conclusions]

        metrics = {
            # align frontend naming
            "nodes": len(nodes),
            "edges": len(edges),
            "modes": len(results),
            "diverged": legacy != balanced,
        }

        return ScenarioPresentation(
            scenario_id, metrics, legacy, balanced, adaptive, 
            nodes, edges, story_script, story, conclusions
        )

    def _safe_id(self, value: str) -> str:
        return value.strip().lower().replace(" ", "-").replace("_", "-")

    def _node_id(self, scenario_id: str, index: int) -> str:
        return f"{self._safe_id(scenario_id)}-step-{index}"

    def _edge_id(self, scenario_id: str, source_idx: int, target_idx: int) -> str:
        return f"{self._safe_id(scenario_id)}-edge-{source_idx}-to-{target_idx}"

    def _build_nodes(self, scenario_id: str, steps: List[Any]) -> List[FlowNode]:
        nodes = []
        for index, step in enumerate(steps):
            kind = "input" if index == 0 else "output" if index == len(steps) - 1 else "process"
            nodes.append(
                FlowNode(
                    id=self._node_id(scenario_id, index),
                    label=step.text,
                    kind=kind,
                    status=step.status,
                    x=index * 320,
                    y=0,
                )
            )
        return nodes

    def _build_edges(self, scenario_id: str, steps: List[Any]) -> List[FlowEdge]:
        edges = []
        for index in range(1, len(steps)):
            edges.append(
                FlowEdge(
                    id=self._edge_id(scenario_id, index - 1, index),
                    source=self._node_id(scenario_id, index - 1),
                    target=self._node_id(scenario_id, index),
                    status=steps[index].status,
                )
            )
        return edges

    # --- Wave-111 Logic: Choreographing the animation frames ---
    def _build_story_script(self, nodes: List[FlowNode], edges: List[FlowEdge], raw_steps: List[Any]) -> List[StoryStep]:
        script = []
        # Frame 0: Start empty or only show Node 0
        script.append(StoryStep("frame-0", "Initialization", "Establishing telemetry...", [nodes[0].id], []))

        active_nodes = [nodes[0].id]
        active_edges = []

        # Play through each step, accumulating the active path
        for i in range(1, len(nodes)):
            active_nodes.append(nodes[i].id)
            active_edges.append(edges[i-1].id)
            
            script.append(
                StoryStep(
                    id=f"frame-{i}",
                    label=f"Phase {i}: {raw_steps[i].status.capitalize()}",
                    message=raw_steps[i].text,
                    highlight_nodes=list(active_nodes),
                    highlight_edges=list(active_edges),
                )
            )
            
        return script

    @staticmethod
    def _display_hop(value: Any) -> str:
        return str(value) if value is not None else "NONE"