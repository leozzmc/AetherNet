from dataclasses import dataclass


@dataclass(frozen=True)
class LinkModel:
    """
    Data model representing a logical contact-plan link.

    Wave-16 introduces link realism metadata (latency, bandwidth, loss)
    without changing Phase-1 forwarding behavior.

    Estimation convention for Phase-2:
    - 1 simulation tick = 1 second
    """

    source: str
    target: str
    start_time: int
    end_time: int
    one_way_delay_ms: int = 0
    bandwidth_kbit: int = 0
    loss_percent: float = 0.0
    bidirectional: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if self.start_time < 0:
            raise ValueError("start_time must be >= 0")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be > start_time")
        if self.one_way_delay_ms < 0:
            raise ValueError("one_way_delay_ms must be >= 0")
        if self.bandwidth_kbit < 0:
            raise ValueError("bandwidth_kbit must be >= 0")
        if not (0.0 <= self.loss_percent <= 100.0):
            raise ValueError("loss_percent must be between 0.0 and 100.0 inclusive")

    def is_active(self, current_tick: int) -> bool:
        """Half-open interval semantics: start_time <= tick < end_time."""
        return self.start_time <= current_tick < self.end_time

    def duration_ticks(self) -> int:
        """Return contact duration in ticks."""
        return self.end_time - self.start_time

    def estimated_capacity_bytes(self) -> int:
        """
        Estimate link capacity in bytes for the contact window.

        Convention:
        - bandwidth_kbit is kilobits per tick-second
        - 1 tick = 1 second
        """
        return (self.bandwidth_kbit * 1000 * self.duration_ticks()) // 8

    def estimated_capacity_bundles(self, avg_bundle_size_bytes: int) -> int:
        """
        Estimate how many average-sized bundles can fit into this link window.
        """
        if avg_bundle_size_bytes <= 0:
            raise ValueError("avg_bundle_size_bytes must be strictly positive")

        return self.estimated_capacity_bytes() // avg_bundle_size_bytes