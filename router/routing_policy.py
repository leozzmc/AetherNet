from __future__ import annotations

from typing import Optional, Protocol

from router.bundle import Bundle


class RoutingPolicy(Protocol):
    """Wave-37 pluggable routing decision interface."""

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        """Return the next-hop node id, or None if no route is available."""
        ...