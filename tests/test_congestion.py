import json

from metrics.congestion_metrics import CongestionMetrics
from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.store_capacity import StoreCapacityController


def make_bundle(
    b_id: str,
    priority: int,
    created_at: int,
    size_bytes: int = 100,
) -> Bundle:
    return Bundle(
        id=b_id,
        type="data",
        source="node-A",
        destination="node-B",
        priority=priority,
        created_at=created_at,
        ttl_sec=3600,
        size_bytes=size_bytes,
        payload_ref="ref",
    )


def make_contact_manager(tmp_path, contacts=None):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "simulation_duration_sec": 100,
                "contacts": contacts or [],
            }
        ),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


def test_no_drop_when_under_capacity():
    controller = StoreCapacityController(capacity_bytes=500)
    store = [
        make_bundle("b1", priority=10, created_at=0, size_bytes=200),
        make_bundle("b2", priority=10, created_at=1, size_bytes=200),
    ]

    dropped = controller.enforce_capacity(store)

    assert len(dropped) == 0
    assert len(store) == 2


def test_overflow_drops_lowest_priority():
    controller = StoreCapacityController(capacity_bytes=300)
    store = [
        make_bundle("high-pri", priority=100, created_at=0, size_bytes=100),
        make_bundle("mid-pri", priority=50, created_at=0, size_bytes=100),
        make_bundle("low-pri-1", priority=10, created_at=0, size_bytes=100),
        make_bundle("low-pri-2", priority=20, created_at=0, size_bytes=100),
    ]

    dropped = controller.enforce_capacity(store)

    assert len(dropped) == 1
    assert dropped[0].id == "low-pri-1"
    assert len(store) == 3


def test_deterministic_drop_ordering_by_created_at():
    controller = StoreCapacityController(capacity_bytes=200)
    store = [
        make_bundle("newer", priority=10, created_at=5, size_bytes=100),
        make_bundle("older", priority=10, created_at=1, size_bytes=100),
        make_bundle("newest", priority=10, created_at=10, size_bytes=100),
    ]

    dropped = controller.enforce_capacity(store)

    assert len(dropped) == 1
    assert dropped[0].id == "older"


def test_lexical_tie_break_for_equal_bundles():
    controller = StoreCapacityController(capacity_bytes=100)
    store = [
        make_bundle("bundle-Z", priority=10, created_at=0, size_bytes=100),
        make_bundle("bundle-A", priority=10, created_at=0, size_bytes=100),
    ]

    dropped = controller.enforce_capacity(store)

    assert len(dropped) == 1
    assert dropped[0].id == "bundle-A"
    assert store[0].id == "bundle-Z"


def test_congestion_metrics_update_correctly():
    metrics = CongestionMetrics(max_store_bytes=1000)

    metrics.record_drops(0)
    metrics.update_store_bytes(500)

    snap1 = metrics.snapshot()
    assert snap1["overflow_events"] == 0
    assert snap1["bundles_dropped"] == 0
    assert snap1["current_store_bytes"] == 500

    metrics.record_drops(2)
    metrics.update_store_bytes(1000)

    snap2 = metrics.snapshot()
    assert snap2["overflow_events"] == 1
    assert snap2["bundles_dropped"] == 2
    assert snap2["current_store_bytes"] == 1000


def test_router_store_bundle_enforces_capacity_and_updates_metrics(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        store_capacity_bytes=200,
    )

    b1 = make_bundle("b1", priority=100, created_at=0, size_bytes=100)
    b2 = make_bundle("b2", priority=50, created_at=1, size_bytes=100)
    b3 = make_bundle("b3", priority=10, created_at=2, size_bytes=100)

    dropped1 = router.store_bundle(b1)
    dropped2 = router.store_bundle(b2)
    dropped3 = router.store_bundle(b3)

    assert dropped1 == []
    assert dropped2 == []
    assert len(dropped3) == 1
    assert dropped3[0].id == "b3"

    assert [b.id for b in router.store] == ["b1", "b2"]

    snap = router.congestion_metrics.snapshot()
    assert snap["max_store_bytes"] == 200
    assert snap["current_store_bytes"] == 200
    assert snap["overflow_events"] == 1
    assert snap["bundles_dropped"] == 1


def test_router_store_bundle_is_backward_compatible_with_infinite_capacity(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        store_capacity_bytes=None,
    )

    for i in range(5):
        dropped = router.store_bundle(
            make_bundle(f"b{i}", priority=1, created_at=i, size_bytes=150)
        )
        assert dropped == []

    assert len(router.store) == 5

    snap = router.congestion_metrics.snapshot()
    assert snap["max_store_bytes"] is None
    assert snap["current_store_bytes"] == 750
    assert snap["overflow_events"] == 0
    assert snap["bundles_dropped"] == 0