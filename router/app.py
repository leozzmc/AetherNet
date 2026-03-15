from typing import Optional

from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.bundle import Bundle
from routing.routing_table import RoutingTable


class AetherRouter:
    """Minimal coordinator for routing-policy and contact-plan checks."""

    def __init__(
        self,
        contact_manager: ContactManager,
        routing_table: Optional[RoutingTable] = None,
    ):
        self.cm = contact_manager
        self.routing_table = routing_table

    def get_next_hop(self, current_node: str, destination: str) -> str | None:
        """
        Preferred Wave-20 routing lookup entrypoint.

        Priority:
        1. explicit routing table
        2. legacy hardcoded policy fallback
        """
        if self.routing_table is not None:
            routed = self.routing_table.get_next_hop(current_node, destination)
            if routed is not None:
                return routed

        return next_hop_for(current_node, destination)

    def next_hop(self, current_node: str, destination: str) -> str | None:
        """
        Backward-compatible alias retained for older code/tests.
        """
        return self.get_next_hop(current_node, destination)

    def can_forward(self, current_node: str, bundle: Bundle, current_time: int) -> bool:
        next_node = self.get_next_hop(current_node, bundle.destination)
        if not next_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)

    def can_forward_destination(self, current_node: str, destination: str, current_time: int) -> bool:
        next_node = self.get_next_hop(current_node, destination)
        if not next_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)