from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .artifacts import Phase6DemoArtifactBundle, Phase6DemoArtifactBuilder
from .reports import Phase6DemoReport, Phase6DemoReportBuilder


@dataclass(frozen=True)
class Phase6DemoRunResult:
    """
    Deterministic container for a single end-to-end Phase-6 demo execution.
    """

    scenario_name: str
    artifact_bundle: Phase6DemoArtifactBundle
    report: Phase6DemoReport
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        exported_metadata = {
            "bridge_name": self.metadata.get("bridge_name"),
            "bridge_version": self.metadata.get("bridge_version"),
            "scenario_name": self.metadata.get("scenario_name"),
        }

        return {
            "type": "phase6_demo_run_result",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "metadata": exported_metadata,
            "artifact_bundle": self.artifact_bundle.to_dict(),
            "report": self.report.to_dict(),
        }


@dataclass(frozen=True)
class Phase6ComparisonReport:
    """
    Deterministic plain-text artifact comparing two Phase-6 demo runs.
    """

    left_scenario_name: str
    right_scenario_name: str
    text: str
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        exported_metadata = {
            "builder_name": self.metadata.get("builder_name"),
            "builder_version": self.metadata.get("builder_version"),
            "line_count": self.metadata.get("line_count", 0),
            "source_node_id": self.metadata.get("source_node_id"),
            "destination_node_id": self.metadata.get("destination_node_id"),
            "time_index": self.metadata.get("time_index"),
        }

        return {
            "type": "phase6_comparison_report",
            "version": "1.0",
            "left_scenario_name": self.left_scenario_name,
            "right_scenario_name": self.right_scenario_name,
            "text": self.text,
            "metadata": exported_metadata,
        }


class Phase6DemoBridge:
    """
    Minimal adapter for end-to-end Phase-6 demo orchestration.
    """

    def __init__(
        self,
        artifact_builder: Optional[Phase6DemoArtifactBuilder] = None,
        report_builder: Optional[Phase6DemoReportBuilder] = None,
    ) -> None:
        self._artifact_builder = (
            artifact_builder
            if artifact_builder is not None
            else Phase6DemoArtifactBuilder()
        )
        self._report_builder = (
            report_builder if report_builder is not None else Phase6DemoReportBuilder()
        )

    def run_scenario(
        self,
        scenario_name: str,
        source_node_id: str,
        destination_node_id: str,
        time_index: int,
        candidate_link_ids: Optional[List[str]] = None,
    ) -> Phase6DemoRunResult:
        bundle = self._artifact_builder.build_from_registry_name(
            scenario_name=scenario_name,
            source_node_id=source_node_id,
            destination_node_id=destination_node_id,
            time_index=time_index,
            candidate_link_ids=candidate_link_ids,
        )

        report = self._report_builder.build(bundle)

        metadata: Dict[str, Any] = {
            "bridge_name": "Phase6DemoBridge",
            "bridge_version": "1.0",
            "scenario_name": scenario_name,
        }

        return Phase6DemoRunResult(
            scenario_name=scenario_name,
            artifact_bundle=bundle,
            report=report,
            metadata=metadata,
        )


class Phase6ComparisonBuilder:
    """
    Deterministic comparison renderer for two Phase-6 demo runs.
    """

    @staticmethod
    def _format_list(items: List[str]) -> str:
        return ", ".join(sorted(items)) if items else "none"

    @staticmethod
    def _validate_run_alignment(
        left: Phase6DemoRunResult,
        right: Phase6DemoRunResult,
    ) -> None:
        left_ctx = left.artifact_bundle.routing_context
        right_ctx = right.artifact_bundle.routing_context

        if left_ctx.source_node_id != right_ctx.source_node_id:
            raise ValueError("Phase6 comparison requires matching source_node_id")
        if left_ctx.destination_node_id != right_ctx.destination_node_id:
            raise ValueError("Phase6 comparison requires matching destination_node_id")
        if left_ctx.time_index != right_ctx.time_index:
            raise ValueError("Phase6 comparison requires matching time_index")

    def build_from_runs(
        self,
        left: Phase6DemoRunResult,
        right: Phase6DemoRunResult,
    ) -> Phase6ComparisonReport:
        self._validate_run_alignment(left, right)

        lines: List[str] = []

        dec_l = left.artifact_bundle.security_aware_routing_decision
        dec_r = right.artifact_bundle.security_aware_routing_decision
        sig_l = left.artifact_bundle.security_signal_report
        sig_r = right.artifact_bundle.security_signal_report

        ctx_l = left.artifact_bundle.routing_context

        name_l = left.scenario_name
        name_r = right.scenario_name

        lines.append("=== Phase-6 Comparison ===")
        lines.append(f"Scenario A: {name_l}")
        lines.append(f"Scenario B: {name_r}")
        lines.append(f"Route: {ctx_l.source_node_id} -> {ctx_l.destination_node_id}")
        lines.append(f"Time Index: {ctx_l.time_index}")
        lines.append("")

        lines.append("[Preferred Links]")
        pref_l = [d.link_id for d in dec_l.link_decisions if d.decision == "preferred"]
        pref_r = [d.link_id for d in dec_r.link_decisions if d.decision == "preferred"]
        lines.append(f"- A: {self._format_list(pref_l)}")
        lines.append(f"- B: {self._format_list(pref_r)}")
        lines.append("")

        lines.append("[Allowed Links]")
        allow_l = [d.link_id for d in dec_l.link_decisions if d.decision == "allowed"]
        allow_r = [d.link_id for d in dec_r.link_decisions if d.decision == "allowed"]
        lines.append(f"- A: {self._format_list(allow_l)}")
        lines.append(f"- B: {self._format_list(allow_r)}")
        lines.append("")

        lines.append("[Avoid Links]")
        avoid_l = [d.link_id for d in dec_l.link_decisions if d.decision == "avoid"]
        avoid_r = [d.link_id for d in dec_r.link_decisions if d.decision == "avoid"]
        lines.append(f"- A: {self._format_list(avoid_l)}")
        lines.append(f"- B: {self._format_list(avoid_r)}")
        lines.append("")

        lines.append("[High Severity Links]")
        high_l = [s.link_id for s in sig_l.link_signals if s.severity == "high"]
        high_r = [s.link_id for s in sig_r.link_signals if s.severity == "high"]
        lines.append(f"- A: {self._format_list(high_l)}")
        lines.append(f"- B: {self._format_list(high_r)}")
        lines.append("")

        lines.append("[Compromised Node Count]")
        compromised_l = sum(1 for n in sig_l.node_signals if n.compromised)
        compromised_r = sum(1 for n in sig_r.node_signals if n.compromised)
        lines.append(f"- A: {compromised_l}")
        lines.append(f"- B: {compromised_r}")

        report_text = "\n".join(lines)

        metadata: Dict[str, Any] = {
            "builder_name": "Phase6ComparisonBuilder",
            "builder_version": "1.0",
            "line_count": len(lines),
            "source_node_id": ctx_l.source_node_id,
            "destination_node_id": ctx_l.destination_node_id,
            "time_index": ctx_l.time_index,
        }

        return Phase6ComparisonReport(
            left_scenario_name=name_l,
            right_scenario_name=name_r,
            text=report_text,
            metadata=metadata,
        )