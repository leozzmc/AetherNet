import json
import tempfile

from metrics.delivery_metrics import DeliveryMetrics
from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from sim.simulator import create_default_simulator


def make_bundle(b_id: str, destination: str = "ground-station") -> Bundle:
    return Bundle(
        id=b_id,
        type="data",
        source="lunar-node",
        destination=destination,
        priority=100,
        created_at=0,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="ref",
    )


def make_contact_manager(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({"simulation_duration_sec": 100, "contacts": []}),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


def test_first_delivery_recorded_correctly():
    metrics = DeliveryMetrics(expected_total_bundles=10)

    result = metrics.record_delivery("bundle-A", current_time=15)

    assert result == "first_delivery"
    record = metrics._records["bundle-A"]
    assert record.bundle_id == "bundle-A"
    assert record.first_delivery_time == 15
    assert record.delivery_count == 1


def test_duplicate_delivery_counted_separately():
    metrics = DeliveryMetrics(expected_total_bundles=10)

    metrics.record_delivery("bundle-A", current_time=15)
    result = metrics.record_delivery("bundle-A", current_time=45)

    assert result == "duplicate_delivery"

    record = metrics._records["bundle-A"]
    assert record.first_delivery_time == 15
    assert record.delivery_count == 2
    assert metrics.duplicate_deliveries == 1


def test_delivery_count_increments_deterministically():
    metrics = DeliveryMetrics()

    metrics.record_delivery("bundle-B", 10)
    metrics.record_delivery("bundle-B", 20)
    metrics.record_delivery("bundle-B", 30)

    record = metrics._records["bundle-B"]
    assert record.delivery_count == 3
    assert record.first_delivery_time == 10


def test_delivery_metrics_snapshot_values_correct():
    metrics = DeliveryMetrics(expected_total_bundles=5)

    metrics.record_delivery("bundle-1", 10)
    metrics.record_delivery("bundle-2", 15)
    metrics.record_delivery("bundle-1", 20)

    snap = metrics.snapshot()

    assert snap["total_delivered"] == 3
    assert snap["unique_delivered"] == 2
    assert snap["duplicate_deliveries"] == 1
    assert snap["delivery_ratio"] == 0.4


def test_snapshot_handles_zero_expected_bundles_gracefully():
    metrics = DeliveryMetrics(expected_total_bundles=0)
    metrics.record_delivery("bundle-1", 10)

    snap = metrics.snapshot()
    assert snap["delivery_ratio"] == 0.0


def test_router_delivery_method_records_accounting_without_affecting_routing(tmp_path):
    router = AetherRouter(contact_manager=make_contact_manager(tmp_path))
    bundle = make_bundle("bundle-1")

    result = router.deliver_bundle(bundle, current_time=50)

    assert result == "first_delivery"
    snap = router.delivery_metrics.snapshot()
    assert snap["total_delivered"] == 1
    assert snap["unique_delivered"] == 1
    assert router.get_next_hop("lunar-node", "ground-station") == "leo-relay"


def test_simulator_integration_records_final_delivery_events():
    plan = {
        "simulation_duration_sec": 5,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 0,
                "end_time": 5,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 0,
                "end_time": 5,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = plan_file.name

    with tempfile.TemporaryDirectory() as tmpstore:
        simulator, bundles = create_default_simulator(
            plan_path=plan_path,
            store_dir=tmpstore,
            scenario_name="wave51_delivery_accounting_test",
            simulation_end_override=5,
        )

        simulator.run()

        snap = simulator.router.delivery_metrics.snapshot()
        assert snap["unique_delivered"] == len(bundles)
        assert snap["total_delivered"] == len(bundles)
        assert snap["duplicate_deliveries"] == 0