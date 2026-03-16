import json

from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.routing_policies import LegacyRoutingPolicy, StaticRoutingPolicy
from routing.routing_table import RoutingTable


def make_bundle(destination: str = "ground-station", next_hop: str | None = None) -> Bundle:
    return Bundle(
        id="tel-001",
        type="telemetry",
        source="lunar-node",
        destination=destination,
        priority=100,
        created_at=0,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="demo",
        next_hop=next_hop,
    )


def make_contact_manager(tmp_path, contacts=None):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "simulation_duration_sec": 10,
                "contacts": contacts or [],
            }
        ),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


# --- Wave-37 Legacy and Basic Compatibility Tests ---


def test_legacy_policy_preserves_original_static_route():
    policy = LegacyRoutingPolicy()

    next_hop = policy.select_next_hop(
        current_node="lunar-node",
        bundle=make_bundle(destination="ground-station"),
        current_time=10,
    )

    assert next_hop == "leo-relay"


def test_static_policy_uses_routing_table_with_current_node_context():
    policy = StaticRoutingPolicy(
        RoutingTable(
            {
                "lunar-node": {"ground-station": "relay-a"},
                "relay-a": {"ground-station": "relay-b"},
            }
        )
    )

    first_hop = policy.select_next_hop(
        current_node="lunar-node",
        bundle=make_bundle(destination="ground-station"),
        current_time=10,
    )
    second_hop = policy.select_next_hop(
        current_node="relay-a",
        bundle=make_bundle(destination="ground-station"),
        current_time=11,
    )

    assert first_hop == "relay-a"
    assert second_hop == "relay-b"


def test_router_defaults_to_legacy_policy_when_nothing_is_injected(tmp_path):
    router = AetherRouter(contact_manager=make_contact_manager(tmp_path))

    assert router.get_next_hop("lunar-node", "ground-station") == "leo-relay"


def test_router_uses_static_policy_implicitly_when_routing_table_is_provided(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
    )

    assert router.get_next_hop("node-A", "node-C") == "node-B"


def test_router_accepts_explicit_policy_override_over_routing_table(tmp_path):
    class NullPolicy:
        def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> str | None:
            return None

    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
        routing_policy=NullPolicy(),
    )

    assert router.get_next_hop("node-A", "node-C") is None


def test_can_forward_is_deterministic_when_policy_returns_none(tmp_path):
    class NullPolicy:
        def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> str | None:
            return None

    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_policy=NullPolicy(),
    )

    assert router.can_forward("lunar-node", make_bundle(), current_time=3) is False


# --- Wave-38 Static Routing Baseline Tests ---


def test_static_policy_returns_none_at_destination():
    policy = StaticRoutingPolicy(RoutingTable({"ground-station": {"other": "relay"}}))
    bundle = make_bundle(destination="ground-station")

    assert policy.select_next_hop("ground-station", bundle, 0) is None


def test_static_policy_returns_none_for_unknown_destination():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"known-dest": "relay"}}))
    bundle = make_bundle(destination="unknown-dest")

    assert policy.select_next_hop("lunar-node", bundle, 0) is None


def test_static_policy_returns_none_for_unknown_source():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"ground-station": "relay"}}))
    bundle = make_bundle(destination="ground-station")

    assert policy.select_next_hop("unknown-node", bundle, 0) is None


def test_static_policy_honors_explicit_bundle_next_hop_override():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"ground-station": "standard-relay"}}))
    bundle = make_bundle(destination="ground-station", next_hop="emergency-relay")

    assert policy.select_next_hop("lunar-node", bundle, 0) == "emergency-relay"


def test_router_can_forward_true_when_static_route_and_contact_exist(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(
            tmp_path,
            contacts=[
                {
                    "source": "node-A",
                    "target": "node-B",
                    "start_time": 0,
                    "end_time": 10,
                    "one_way_delay_ms": 10,
                    "bandwidth_kbit": 100,
                    "bidirectional": False,
                }
            ],
        ),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
    )

    bundle = Bundle(
        id="bundle-1",
        type="telemetry",
        source="node-A",
        destination="node-C",
        priority=10,
        created_at=0,
        ttl_sec=100,
        size_bytes=100,
        payload_ref="demo",
    )

    assert router.can_forward("node-A", bundle, current_time=5) is True


def test_router_can_forward_returns_false_at_destination_even_if_contact_exists(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(
            tmp_path,
            contacts=[
                {
                    "source": "ground-station",
                    "target": "relay",
                    "start_time": 0,
                    "end_time": 10,
                    "one_way_delay_ms": 10,
                    "bandwidth_kbit": 100,
                    "bidirectional": False,
                }
            ],
        ),
        routing_table=RoutingTable({"ground-station": {"mars": "relay"}}),
    )
    bundle = make_bundle(destination="ground-station")

    # Even though a contact exists from ground-station -> relay,
    # the policy must return None because the bundle is already at destination.
    assert router.can_forward("ground-station", bundle, current_time=5) is False