from __future__ import annotations

from typing import Optional

from router.contact_manager import ContactManager
from router.bundle import Bundle
from router.routing_policy import RoutingPolicy
from router.routing_policies import LegacyRoutingPolicy, StaticRoutingPolicy
from routing.routing_table import RoutingTable


class AetherRouter:
    """Minimal coordinator for routing-policy and contact-plan checks."""

    def __init__(
        self,
        contact_manager: ContactManager,
        routing_table: Optional[RoutingTable] = None,
        routing_policy: Optional[RoutingPolicy] = None,
    ):
        self.cm = contact_manager
        self.routing_table = routing_table
        self.routing_policy = routing_policy or self._default_policy(routing_table)

    @staticmethod
    def _default_policy(routing_table: Optional[RoutingTable]) -> RoutingPolicy:
        """
        Preserve historical behavior:
        - explicit routing table takes precedence when provided
        - otherwise fall back to legacy static route policy
        """
        if routing_table is not None:
            return StaticRoutingPolicy(routing_table)
        return LegacyRoutingPolicy()

    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        current_time: int = 0,
    ) -> str | None:
        """
        Preferred routing lookup entrypoint.

        Backward compatibility:
        - older callers may omit current_time and will default to 0
        - time-aware policies may use current_time when provided
        """
        bundle = Bundle(
            id="__routing_lookup__",
            type="routing-lookup",
            source=current_node,
            destination=destination,
            priority=0,
            created_at=0,
            ttl_sec=1,
            size_bytes=0,
            payload_ref="routing-lookup",
        )
        return self.routing_policy.select_next_hop(
            current_node=current_node,
            bundle=bundle,
            current_time=current_time,
        )

    def next_hop(
        self,
        current_node: str,
        destination: str,
        current_time: int = 0,
    ) -> str | None:
        """
        Backward-compatible alias retained for older code/tests.
        """
        return self.get_next_hop(current_node, destination, current_time=current_time)

    def can_forward(self, current_node: str, bundle: Bundle, current_time: int) -> bool:
        next_node = self.routing_policy.select_next_hop(
            current_node=current_node,
            bundle=bundle,
            current_time=current_time,
        )
        if not next_node or next_node == current_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)

    def can_forward_destination(self, current_node: str, destination: str, current_time: int) -> bool:
        next_node = self.get_next_hop(current_node, destination, current_time=current_time)
        if not next_node or next_node == current_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)