import json

from metrics.congestion_metrics import CongestionMetrics
from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.eviction_policy import DropLowestPriorityPolicy, DropOldestPolicy


def make_bundle(b_id: str, priority: int, created_at: int, size_bytes: int = 100) -> Bundle:
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


def make_contact_manager(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({"simulation_duration_sec": 100, "contacts": []}),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


def test_drop_oldest_policy_evicts_deterministically():
    policy = DropOldestPolicy()

    store = [
        make_bundle("new-high-pri", priority=100, created_at=10, size_bytes=100),
        make_bundle("old-high-pri", priority=100, created_at=1, size_bytes=100),
        make_bundle("new-low-pri", priority=10, created_at=15, size_bytes=100),
        make_bundle("old-low-pri", priority=10, created_at=2, size_bytes=100),
    ]

    victims = policy.choose_victims(store, bytes_to_free=200)

    assert len(victims) == 2
    assert victims[0].id == "old-high-pri"
    assert victims[1].id == "old-low-pri"


def test_different_policies_yield_different_results():
    store1 = [
        make_bundle("old-important", priority=100, created_at=1, size_bytes=100),
        make_bundle("new-bulk", priority=10, created_at=10, size_bytes=100),
    ]
    store2 = list(store1)

    policy_lowest_pri = DropLowestPriorityPolicy()
    policy_oldest = DropOldestPolicy()

    victims_pri = policy_lowest_pri.choose_victims(store1, 100)
    victims_old = policy_oldest.choose_victims(store2, 100)

    assert victims_pri[0].id == "new-bulk"
    assert victims_old[0].id == "old-important"


def test_router_integration_with_custom_eviction_policy(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        store_capacity_bytes=200,
        eviction_policy=DropOldestPolicy(),
    )

    router.store_bundle(make_bundle("b1", priority=100, created_at=1))
    router.store_bundle(make_bundle("b2", priority=50, created_at=2))

    dropped = router.store_bundle(make_bundle("b3", priority=10, created_at=3))

    assert len(dropped) == 1
    assert dropped[0].id == "b1"

    snap = router.congestion_metrics.snapshot()
    assert snap["eviction_policy"] == "DropOldestPolicy"
    assert snap["peak_store_bytes"] == 200
    assert snap["store_utilization_ratio"] == 1.0
    assert snap["dropped_bytes"] == 100


def test_peak_store_bytes_is_tracked_accurately(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        store_capacity_bytes=500,
    )

    router.store_bundle(make_bundle("b1", priority=10, created_at=1, size_bytes=200))
    router.store_bundle(make_bundle("b2", priority=10, created_at=2, size_bytes=200))

    router.store.pop()
    router.congestion_metrics.update_store_bytes(200)

    snap = router.congestion_metrics.snapshot()
    assert snap["current_store_bytes"] == 200
    assert snap["peak_store_bytes"] == 400


def test_router_default_eviction_policy_remains_backward_compatible(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        store_capacity_bytes=200,
    )

    router.store_bundle(make_bundle("high", priority=100, created_at=1))
    router.store_bundle(make_bundle("mid", priority=50, created_at=2))
    dropped = router.store_bundle(make_bundle("low", priority=10, created_at=3))

    assert len(dropped) == 1
    assert dropped[0].id == "low"

    snap = router.congestion_metrics.snapshot()
    assert snap["eviction_policy"] == "DropLowestPriorityPolicy"


def test_store_utilization_ratio_is_zero_when_capacity_is_none():
    metrics = CongestionMetrics(max_store_bytes=None)
    metrics.update_store_bytes(500)

    snap = metrics.snapshot()
    assert snap["store_utilization_ratio"] == 0.0