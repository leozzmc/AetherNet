from __future__ import annotations

from typing import Optional

from router.bundle import Bundle
from router.policies import next_hop_for
from router.routing_policy import RoutingPolicy
from routing.routing_table import RoutingTable


class LegacyRoutingPolicy:
    """Preserve the original hardcoded route fallback behavior."""

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        return next_hop_for(current_node, bundle.destination)


class StaticRoutingPolicy:
    """
    Wave-38: Baseline routing policy backed by the existing deterministic RoutingTable.
    Explicitly defines destination arrival and no-route semantics.
    """

    def __init__(self, routing_table: RoutingTable):
        self.routing_table = routing_table

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        # 1. Arrival semantics: Do not forward if we are already at the destination
        if current_node == bundle.destination:
            return None

        # 2. Override semantics: Explicit pinned next_hop takes absolute precedence
        if bundle.next_hop:
            return bundle.next_hop

        # 3. Table lookup semantics: Returns None implicitly if route/source is unknown
        return self.routing_table.get_next_hop(current_node, bundle.destination)