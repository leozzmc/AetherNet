from dataclasses import dataclass
from typing import Any, Dict, List

from .artifacts import Phase6DemoArtifactBundle


@dataclass(frozen=True)
class Phase6DemoReport:
    """
    Wave-86: Deterministic, human-readable presentation artifact for Phase-6 demos.
    Encapsulates the rendered text and strict metadata, completely isolated from
    the generation and decision logic.
    """

    scenario_name: str
    text: str
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation of the rendered report.
        """
        exported_metadata = {
            "builder_name": self.metadata.get("builder_name"),
            "builder_version": self.metadata.get("builder_version"),
            "line_count": self.metadata.get("line_count", 0),
        }

        return {
            "type": "phase6_demo_report",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "text": self.text,
            "metadata": exported_metadata,
        }


class Phase6DemoReportBuilder:
    """
    Deterministic renderer that transforms a Phase6DemoArtifactBundle into
    a stable, structured, human-readable plain-text report.
    """

    @staticmethod
    def _format_list(items: List[str]) -> str:
        """Helper to format lists with a clean fallback for empty states."""
        return ", ".join(items) if items else "none"

    def build(self, bundle: Phase6DemoArtifactBundle) -> Phase6DemoReport:
        lines: List[str] = []

        # Extract commonly used sub-artifacts for readability
        spec = bundle.scenario_spec
        ctx = bundle.routing_context
        obs = ctx.network_observation
        score_rep = bundle.routing_score_report
        sig_rep = bundle.security_signal_report
        dec_rep = bundle.security_aware_routing_decision

        # --- Header ---
        lines.append("=== Phase-6 Demo Report ===")
        lines.append(f"Scenario: {bundle.scenario_name}")
        lines.append(f"Route: {ctx.source_node_id} -> {ctx.destination_node_id}")
        lines.append(f"Time Index: {ctx.time_index}")
        lines.append("")

        # --- Scenario Summary ---
        lines.append("[Scenario Summary]")
        lines.append(f"Reliability Trace: {'enabled' if spec.include_reliability_trace else 'disabled'}")
        lines.append(f"Adversarial Trace: {'enabled' if spec.include_adversarial_trace else 'disabled'}")
        lines.append(f"Candidate Links: {len(ctx.candidate_link_ids)}")
        lines.append("")

        # --- Observed Conditions ---
        lines.append("[Observed Conditions]")
        lines.append(f"Degraded Links: {self._format_list(sorted(obs.degraded_links))}")
        lines.append(f"Jammed Links: {self._format_list(sorted(obs.jammed_links))}")
        lines.append(f"Malicious Drop Links: {self._format_list(sorted(obs.malicious_drop_links))}")
        lines.append(f"Compromised Nodes: {self._format_list(sorted(obs.compromised_nodes))}")
        lines.append("")

        # --- Probabilistic Scores ---
        lines.append("[Probabilistic Scores]")
        if not score_rep.link_scores:
            lines.append("none")
        else:
            sorted_scores = sorted(score_rep.link_scores, key=lambda s: s.link_id)
            for score in sorted_scores:
                score_str = f"{score.link_id} -> score={score.final_score:.2f} success={score.estimated_success_probability:.2f}"
                if score.reasons:
                    score_str += f" reasons={self._format_list(sorted(score.reasons))}"
                lines.append(score_str)
        lines.append("")

        # --- Security Signals ---
        lines.append("[Security Signals]")
        has_signals = False
        
        sorted_link_sigs = sorted(sig_rep.link_signals, key=lambda s: s.link_id)
        for l_sig in sorted_link_sigs:
            lines.append(f"{l_sig.link_id} -> {l_sig.severity}")
            has_signals = True

        sorted_node_sigs = sorted(sig_rep.node_signals, key=lambda s: s.node_id)
        for n_sig in sorted_node_sigs:
            # We explicitly highlight compromised nodes in the signal readout
            if n_sig.compromised:
                lines.append(f"{n_sig.node_id} -> {n_sig.severity} (compromised)")
                has_signals = True
            elif n_sig.severity != "low":
                # Fallback for future node severities
                lines.append(f"{n_sig.node_id} -> {n_sig.severity}")
                has_signals = True

        if not has_signals:
            lines.append("none")
        lines.append("")

        # --- Security-Aware Decision ---
        lines.append("[Security-Aware Decision]")
        
        # We manually group them to ensure the presentation order is strict
        pref_links = sorted([d.link_id for d in dec_rep.link_decisions if d.decision == "preferred"])
        allow_links = sorted([d.link_id for d in dec_rep.link_decisions if d.decision == "allowed"])
        avoid_links = sorted([d.link_id for d in dec_rep.link_decisions if d.decision == "avoid"])

        lines.append(f"Preferred: {self._format_list(pref_links)}")
        lines.append(f"Allowed: {self._format_list(allow_links)}")
        lines.append(f"Avoid: {self._format_list(avoid_links)}")

        # Join into final text blob
        report_text = "\n".join(lines)

        metadata: Dict[str, Any] = {
            "builder_name": "Phase6DemoReportBuilder",
            "builder_version": "1.0",
            "line_count": len(lines),
        }

        return Phase6DemoReport(
            scenario_name=bundle.scenario_name,
            text=report_text,
            metadata=metadata,
        )