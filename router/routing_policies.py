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
    """Route lookup backed by the existing deterministic RoutingTable."""

    def __init__(self, routing_table: RoutingTable):
        self.routing_table = routing_table

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        return self.routing_table.get_next_hop(current_node, bundle.destination)