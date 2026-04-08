from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aether_routing_context import RoutingContext, RoutingContextBuilder
from aether_routing_scoring import ProbabilisticScorer, RoutingScoreReport
from aether_scenarios import GeneratedScenario, ScenarioGenerator, ScenarioSpec
from aether_security_routing import (
    SecurityAwareRoutingDecision,
    SecurityAwareRoutingEngine,
)
from aether_security_signals import SecuritySignalBuilder, SecuritySignalReport

from .registry import Phase6ScenarioRegistry


@dataclass(frozen=True)
class Phase6DemoArtifactBundle:
    """
    Deterministic container representing the complete suite of artifacts
    generated for a single Phase-6 demo scenario execution.
    """

    scenario_name: str
    scenario_spec: ScenarioSpec
    generated_scenario: GeneratedScenario
    routing_context: RoutingContext
    routing_score_report: RoutingScoreReport
    security_signal_report: SecuritySignalReport
    security_aware_routing_decision: SecurityAwareRoutingDecision
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    @staticmethod
    def _export_scenario_spec(spec: ScenarioSpec) -> Dict[str, Any]:
        """
        Export an explicit, stable ScenarioSpec schema for demo artifacts.

        This avoids exposing future ScenarioSpec fields automatically via asdict().
        """
        return {
            "scenario_name": spec.scenario_name,
            "master_seed": spec.master_seed,
            "node_count": spec.node_count,
            "link_count": spec.link_count,
            "time_horizon": spec.time_horizon,
            "include_reliability_trace": spec.include_reliability_trace,
            "include_adversarial_trace": spec.include_adversarial_trace,
            "loss_probability": spec.loss_probability,
            "degradation_probability": spec.degradation_probability,
            "max_extra_delay_ms": spec.max_extra_delay_ms,
            "jamming_probability": spec.jamming_probability,
            "malicious_drop_probability": spec.malicious_drop_probability,
            "node_compromise_probability": spec.node_compromise_probability,
            "max_injected_delay_ms": spec.max_injected_delay_ms,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation of the complete artifact bundle.
        """
        exported_metadata = {
            "builder_name": self.metadata.get("builder_name"),
            "builder_version": self.metadata.get("builder_version"),
            "scenario_name": self.metadata.get("scenario_name"),
            "source_node_id": self.metadata.get("source_node_id"),
            "destination_node_id": self.metadata.get("destination_node_id"),
            "time_index": self.metadata.get("time_index"),
            "candidate_link_count": self.metadata.get("candidate_link_count", 0),
        }

        return {
            "type": "phase6_demo_artifact_bundle",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "metadata": exported_metadata,
            "scenario_spec": self._export_scenario_spec(self.scenario_spec),
            "generated_scenario": self.generated_scenario.to_dict(),
            "routing_context": self.routing_context.to_dict(),
            "routing_score_report": self.routing_score_report.to_dict(),
            "security_signal_report": self.security_signal_report.to_dict(),
            "security_aware_routing_decision": (
                self.security_aware_routing_decision.to_dict()
            ),
        }


class Phase6DemoArtifactBuilder:
    """
    Adapter and orchestration layer for Phase-6 demo scenarios.

    This builder connects a ScenarioSpec (or registry scenario name) to the
    deterministic Phase-6 pipeline and packages the outputs into a stable bundle.
    """

    def __init__(
        self,
        scenario_generator: Optional[ScenarioGenerator] = None,
        context_builder: Optional[RoutingContextBuilder] = None,
        scorer: Optional[ProbabilisticScorer] = None,
        signal_builder: Optional[SecuritySignalBuilder] = None,
        decision_engine: Optional[SecurityAwareRoutingEngine] = None,
    ) -> None:
        self._scenario_generator = (
            scenario_generator if scenario_generator is not None else ScenarioGenerator()
        )
        self._context_builder = (
            context_builder if context_builder is not None else RoutingContextBuilder()
        )
        self._scorer = scorer if scorer is not None else ProbabilisticScorer()
        self._signal_builder = (
            signal_builder if signal_builder is not None else SecuritySignalBuilder()
        )
        self._decision_engine = (
            decision_engine
            if decision_engine is not None
            else SecurityAwareRoutingEngine()
        )

    @staticmethod
    def _validate_inputs(
        source_node_id: str,
        destination_node_id: str,
        time_index: int,
    ) -> None:
        if not source_node_id.strip():
            raise ValueError("source_node_id must be a non-empty string")
        if not destination_node_id.strip():
            raise ValueError("destination_node_id must be a non-empty string")
        if time_index < 0:
            raise ValueError(f"time_index cannot be negative, got {time_index}")

    def build_from_spec(
        self,
        spec: ScenarioSpec,
        source_node_id: str,
        destination_node_id: str,
        time_index: int,
        candidate_link_ids: Optional[List[str]] = None,
    ) -> Phase6DemoArtifactBundle:
        self._validate_inputs(
            source_node_id=source_node_id,
            destination_node_id=destination_node_id,
            time_index=time_index,
        )

        generated_scenario = self._scenario_generator.generate(spec)

        routing_context = self._context_builder.build(
            scenario=generated_scenario,
            time_index=time_index,
            source_node_id=source_node_id,
            destination_node_id=destination_node_id,
            candidate_link_ids=candidate_link_ids,
        )

        routing_score_report = self._scorer.score(routing_context)

        security_signal_report = self._signal_builder.build(
            context=routing_context,
            score_report=routing_score_report,
        )

        security_aware_routing_decision = self._decision_engine.build_decision(
            context=routing_context,
            score_report=routing_score_report,
            signal_report=security_signal_report,
        )

        metadata: Dict[str, Any] = {
            "builder_name": "Phase6DemoArtifactBuilder",
            "builder_version": "1.0",
            "scenario_name": spec.scenario_name,
            "source_node_id": source_node_id,
            "destination_node_id": destination_node_id,
            "time_index": time_index,
            "candidate_link_count": len(routing_context.candidate_link_ids),
        }

        return Phase6DemoArtifactBundle(
            scenario_name=spec.scenario_name,
            scenario_spec=spec,
            generated_scenario=generated_scenario,
            routing_context=routing_context,
            routing_score_report=routing_score_report,
            security_signal_report=security_signal_report,
            security_aware_routing_decision=security_aware_routing_decision,
            metadata=metadata,
        )

    def build_from_registry_name(
        self,
        scenario_name: str,
        source_node_id: str,
        destination_node_id: str,
        time_index: int,
        candidate_link_ids: Optional[List[str]] = None,
    ) -> Phase6DemoArtifactBundle:
        spec = Phase6ScenarioRegistry.get_spec_by_name(scenario_name)
        return self.build_from_spec(
            spec=spec,
            source_node_id=source_node_id,
            destination_node_id=destination_node_id,
            time_index=time_index,
            candidate_link_ids=candidate_link_ids,
        )