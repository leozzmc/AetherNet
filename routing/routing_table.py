from typing import Dict, Optional


class RoutingTable:
    """
    Static routing table abstraction for AetherNet.
    Provides deterministic next-hop lookup without dynamic discovery overhead.
    """

    def __init__(self, routes: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        self._routes = routes or {}

    def get_next_hop(self, source: str, destination: str) -> Optional[str]:
        if source in self._routes and destination in self._routes[source]:
            return self._routes[source][destination]
        return None

    def has_route(self, source: str, destination: str) -> bool:
        return self.get_next_hop(source, destination) is not None