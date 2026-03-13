from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.bundle import Bundle


class AetherRouter:
    """Minimal coordinator for routing-policy and contact-plan checks."""

    def __init__(self, contact_manager: ContactManager):
        self.cm = contact_manager

    def next_hop(self, current_node: str, destination: str) -> str | None:
        return next_hop_for(current_node, destination)

    def can_forward(self, current_node: str, bundle: Bundle, current_time: int) -> bool:
        next_node = self.next_hop(current_node, bundle.destination)
        if not next_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)

    def can_forward_destination(self, current_node: str, destination: str, current_time: int) -> bool:
        next_node = self.next_hop(current_node, destination)
        if not next_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)