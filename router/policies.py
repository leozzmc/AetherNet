from typing import Optional

_ROUTE = ["lunar-node", "leo-relay", "ground-station"]


def next_hop_for(current_node: str, destination: str) -> Optional[str]:
    """Return the next hop on the static MVP route, or None if no valid route exists."""
    if current_node not in _ROUTE or destination not in _ROUTE:
        return None

    current_idx = _ROUTE.index(current_node)
    dest_idx = _ROUTE.index(destination)

    if current_idx >= dest_idx:
        return None

    return _ROUTE[current_idx + 1]


def is_final_hop(current_node: str, destination: str) -> bool:
    """Return True if the next hop from current_node reaches the final destination."""
    return next_hop_for(current_node, destination) == destination