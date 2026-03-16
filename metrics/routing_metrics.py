from __future__ import annotations

from collections import defaultdict
from typing import Dict

from router.routing_decision import RoutingDecision


KNOWN_ROUTING_REASONS = (
    "at_destination",
    "explicit_override_open",
    "explicit_override_blocked",
    "no_route",
    "no_future_route",
    "contact_blocked",
    "selected_legacy_route",
    "selected_static_route",
    "selected_scored_candidate",
    "selected_future_route",
)


class RoutingMetricsCollector:
    """
    Wave-42: Deterministic accumulator for routing decisions.

    This collector is intentionally external to routing policies so policies remain
    stateless and backward-compatible.
    """

    def __init__(self, policy_name: str = "unknown_policy"):
        self.policy_name = policy_name
        self.total_lookups: int = 0
        self.reason_counts: Dict[str, int] = defaultdict(int)
        self.next_hop_counts: Dict[str, int] = defaultdict(int)

    def record(self, decision: RoutingDecision) -> None:
        """Record a RoutingDecision."""
        self.total_lookups += 1
        self.reason_counts[decision.reason] += 1

        if decision.next_hop is None:
            self.next_hop_counts["None"] += 1
        else:
            self.next_hop_counts[decision.next_hop] += 1

    def snapshot(self) -> dict:
        """
        Produce a deterministic, serializable summary.

        Important:
        - known reasons are always present, even if their count is 0
        - output order is stabilized for easier comparison in tests/reports
        """
        reason_counts = {reason: self.reason_counts.get(reason, 0) for reason in KNOWN_ROUTING_REASONS}

        # Preserve any unexpected custom reasons too, but append them deterministically.
        extra_reasons = sorted(k for k in self.reason_counts.keys() if k not in reason_counts)
        for reason in extra_reasons:
            reason_counts[reason] = self.reason_counts[reason]

        next_hop_counts = {}
        if "None" in self.next_hop_counts:
            next_hop_counts["None"] = self.next_hop_counts["None"]

        for hop in sorted(k for k in self.next_hop_counts.keys() if k != "None"):
            next_hop_counts[hop] = self.next_hop_counts[hop]

        return {
            "policy_name": self.policy_name,
            "total_lookups": self.total_lookups,
            "reason_counts": reason_counts,
            "next_hop_counts": next_hop_counts,
        }