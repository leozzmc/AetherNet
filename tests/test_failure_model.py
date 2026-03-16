import json

from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.failure_model import FailureModel
from routing.routing_table import RoutingTable


def make_bundle() -> Bundle:
    return Bundle(
        id="tel-001",
        type="telemetry",
        source="node-A",
        destination="node-C",
        priority=100,
        created_at=0,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="demo",
    )


def make_contact_manager(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "simulation_duration_sec": 100,
                "contacts": [
                    {
                        "source": "node-A",
                        "target": "node-B",
                        "start_time": 0,
                        "end_time": 100,
                        "one_way_delay_ms": 0,
                        "bandwidth_kbit": 100,
                        "bidirectional": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


def test_failure_model_node_outage_semantics():
    fm = FailureModel(node_outages={"node-B": [(10, 30)]})

    assert fm.is_node_available("node-B", 5) is True
    assert fm.is_node_available("node-B", 10) is False
    assert fm.is_node_available("node-B", 20) is False
    assert fm.is_node_available("node-B", 30) is True

    assert fm.is_node_available("node-A", 15) is True


def test_failure_model_link_failure_semantics():
    fm = FailureModel(link_failures=[("node-A", "node-B", 10, 30)])

    assert fm.is_link_available("node-A", "node-B", 5) is True
    assert fm.is_link_available("node-A", "node-B", 15) is False
    assert fm.is_link_available("node-A", "node-B", 30) is True

    assert fm.is_link_available("node-B", "node-A", 15) is True


def test_failure_model_forwarding_permission_gate():
    fm = FailureModel(
        node_outages={"node-A": [(10, 20)]},
        link_failures=[("node-A", "node-B", 30, 40)],
    )

    assert fm.is_forwarding_permitted("node-A", "node-B", 15) is False

    fm.node_outages["node-B"] = [(50, 60)]
    assert fm.is_forwarding_permitted("node-A", "node-B", 55) is False

    assert fm.is_forwarding_permitted("node-A", "node-B", 35) is False

    assert fm.is_forwarding_permitted("node-A", "node-B", 5) is True
    assert fm.is_forwarding_permitted("node-A", "node-B", 25) is True
    assert fm.is_forwarding_permitted("node-A", "node-B", 45) is True


def test_router_integration_no_failure_model_preserves_behavior(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
    )

    bundle = make_bundle()
    assert router.can_forward("node-A", bundle, 15) is True


def test_router_integration_node_outage_blocks_then_recovers(tmp_path):
    fm = FailureModel(node_outages={"node-B": [(10, 30)]})
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
        failure_model=fm,
    )

    bundle = make_bundle()

    assert router.can_forward("node-A", bundle, 5) is True
    assert router.can_forward("node-A", bundle, 15) is False
    assert router.can_forward("node-A", bundle, 35) is True


def test_router_integration_link_failure_blocks_then_recovers(tmp_path):
    fm = FailureModel(link_failures=[("node-A", "node-B", 50, 80)])
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
        failure_model=fm,
    )

    bundle = make_bundle()

    assert router.can_forward("node-A", bundle, 40) is True
    assert router.can_forward("node-A", bundle, 60) is False
    assert router.can_forward("node-A", bundle, 85) is True


def test_router_can_forward_destination_respects_failure_model(tmp_path):
    fm = FailureModel(node_outages={"node-B": [(10, 30)]})
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
        failure_model=fm,
    )

    assert router.can_forward_destination("node-A", "node-C", 5) is True
    assert router.can_forward_destination("node-A", "node-C", 15) is False
    assert router.can_forward_destination("node-A", "node-C", 35) is True


def test_failure_model_is_deterministic_for_repeated_calls():
    fm = FailureModel(
        node_outages={"relay-1": [(10, 20)]},
        link_failures=[("node-A", "relay-1", 30, 40)],
    )

    result_1 = fm.is_forwarding_permitted("node-A", "relay-1", 15)
    result_2 = fm.is_forwarding_permitted("node-A", "relay-1", 15)
    result_3 = fm.is_forwarding_permitted("node-A", "relay-1", 35)
    result_4 = fm.is_forwarding_permitted("node-A", "relay-1", 35)

    assert result_1 is False
    assert result_2 is False
    assert result_3 is False
    assert result_4 is False