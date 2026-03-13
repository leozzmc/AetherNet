import json
import tempfile
from pathlib import Path

import pytest

from router.bundle import Bundle, BundleStatus
from router.contact_manager import ContactManager
from router.app import AetherRouter
from bundle_queue.priority_queue import StrictPriorityQueue
from store.store import DTNStore
from sim.event_loop import SimulationClock
from sim.simulator import Simulator
from metrics.exporter import MetricsCollector


@pytest.fixture
def mock_multihop_contact_manager():
    plan = {
        "simulation_duration_sec": 15,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 2,
                "end_time": 5,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 8,
                "end_time": 12,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        json.dump(plan, f)
        tmp_path = Path(f.name)

    try:
        yield ContactManager(str(tmp_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_end_to_end_delivery(mock_multihop_contact_manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DTNStore(tmpdir)
        lunar_q = StrictPriorityQueue()
        relay_q = StrictPriorityQueue()
        metrics = MetricsCollector()
        clock = SimulationClock(0, 10)

        b_tel = Bundle(
            id="tel-1",
            type="telemetry",
            source="lunar-node",
            destination="ground-station",
            priority=100,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="ref",
        )
        b_sci = Bundle(
            id="sci-1",
            type="science",
            source="lunar-node",
            destination="ground-station",
            priority=50,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="ref",
        )

        lunar_q.enqueue(b_sci)
        lunar_q.enqueue(b_tel)
        store.save_bundle(b_sci)
        store.save_bundle(b_tel)

        sim = Simulator(AetherRouter(mock_multihop_contact_manager), store, lunar_q, relay_q, clock, metrics)

        # t=2: first hop opens, telemetry should move to relay and remain STORED
        sim.tick(2)
        assert store.load_bundle("tel-1").status == BundleStatus.STORED
        assert relay_q.size() == 1

        # t=3: science follows to relay
        sim.tick(3)
        assert store.load_bundle("sci-1").status == BundleStatus.STORED
        assert relay_q.size() == 2

        # t=8: second hop opens, telemetry delivered first
        sim.tick(8)
        assert store.load_bundle("tel-1").status == BundleStatus.DELIVERED
        assert relay_q.size() == 1

        # t=9: science delivered next
        sim.tick(9)
        assert store.load_bundle("sci-1").status == BundleStatus.DELIVERED
        assert relay_q.size() == 0