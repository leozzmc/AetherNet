import json

from routing.routing_table import RoutingTable
from router.app import AetherRouter
from router.contact_manager import ContactManager


def test_routing_table_basic_lookup():
    routes = {
        "lunar-node": {
            "ground-station": "leo-relay",
            "mars-base": "deep-space-relay",
        },
        "leo-relay": {
            "ground-station": "ground-station",
        },
    }
    rt = RoutingTable(routes)

    assert rt.get_next_hop("lunar-node", "ground-station") == "leo-relay"
    assert rt.get_next_hop("leo-relay", "ground-station") == "ground-station"

    assert rt.has_route("lunar-node", "mars-base") is True
    assert rt.has_route("lunar-node", "unknown-dest") is False
    assert rt.get_next_hop("unknown-src", "ground-station") is None


def test_router_abstraction_with_table(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"simulation_duration_sec": 10, "contacts": []}), encoding="utf-8")
    cm = ContactManager(str(plan_path))

    rt = RoutingTable({
        "node-A": {"node-C": "node-B"}
    })

    router = AetherRouter(contact_manager=cm, routing_table=rt)

    assert router.get_next_hop("node-A", "node-C") == "node-B"


def test_router_abstraction_fallback(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"simulation_duration_sec": 10, "contacts": []}), encoding="utf-8")
    cm = ContactManager(str(plan_path))

    router = AetherRouter(contact_manager=cm)

    # Backward-compatible fallback to legacy policy
    assert router.get_next_hop("lunar-node", "ground-station") == "leo-relay"

    # Unknown legacy route still returns None
    assert router.get_next_hop("lunar-node", "deep-space-network") is None