from router.bundle import Bundle, BundleStatus
from router.policies import is_final_hop

class ForwardingEngine:
    """Handles state transitions for forwarding operations."""

    @staticmethod
    def begin_forward(bundle: Bundle) -> None:
        """Transitions bundle to FORWARDING state."""
        bundle.transition(BundleStatus.FORWARDING)

    @staticmethod
    def complete_forward(bundle: Bundle, current_node: str) -> None:
        """
        Transitions bundle to DELIVERED if it reached its destination,
        otherwise marks it as STORED at the intermediate relay.
        """
        if is_final_hop(current_node, bundle.destination):
            bundle.transition(BundleStatus.DELIVERED)
        else:
            bundle.transition(BundleStatus.STORED)