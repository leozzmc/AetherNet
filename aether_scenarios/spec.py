from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioSpec:
    """
    Explicit blueprint for deterministic scenario composition.
    """

    scenario_name: str
    master_seed: int
    node_count: int
    link_count: int
    time_horizon: int

    include_reliability_trace: bool = False
    include_adversarial_trace: bool = False

    loss_probability: float = 0.0
    degradation_probability: float = 0.0
    max_extra_delay_ms: int = 0

    jamming_probability: float = 0.0
    malicious_drop_probability: float = 0.0
    node_compromise_probability: float = 0.0
    max_injected_delay_ms: int = 0

    def __post_init__(self) -> None:
        if not self.scenario_name.strip():
            raise ValueError("scenario_name must be a non-empty string")
        if self.node_count < 0:
            raise ValueError(f"node_count cannot be negative, got {self.node_count}")
        if self.link_count < 0:
            raise ValueError(f"link_count cannot be negative, got {self.link_count}")
        if self.time_horizon < 0:
            raise ValueError(f"time_horizon cannot be negative, got {self.time_horizon}")