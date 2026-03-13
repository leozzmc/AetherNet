import json
import tempfile
from pathlib import Path

import pytest

from router.bundle import Bundle, BundleStatus
from router.contact_manager import ContactManager
from bundle_queue.priority_queue import StrictPriorityQueue
from store.store import DTNStore
from sim.event_loop import SimulationClock
from sim.simulator import Simulator


@pytest.fixture
def mock_contact_manager():
    plan = {
        "simulation_duration_sec": 10,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 2,
                "end_time": 5,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            }
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


def test_simulator_holds_when_link_down(mock_contact_manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DTNStore(tmpdir)
        queue = StrictPriorityQueue()
        clock = SimulationClock(0, 5)

        b = Bundle(
            id="tel-1",
            type="telemetry",
            source="lunar-node",
            destination="ground",
            priority=100,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="ref",
        )
        queue.enqueue(b)
        store.save_bundle(b)

        sim = Simulator(mock_contact_manager, store, queue, clock)
        sim.tick(0)

        assert queue.size() == 1
        assert store.load_bundle("tel-1").status == BundleStatus.QUEUED


def test_simulator_forwards_telemetry_first(mock_contact_manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DTNStore(tmpdir)
        queue = StrictPriorityQueue()
        clock = SimulationClock(0, 5)

        b_sci = Bundle(
            id="sci-1",
            type="science",
            source="lunar-node",
            destination="ground",
            priority=50,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="ref",
        )
        b_tel = Bundle(
            id="tel-1",
            type="telemetry",
            source="lunar-node",
            destination="ground",
            priority=100,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="ref",
        )

        queue.enqueue(b_sci)
        queue.enqueue(b_tel)
        store.save_bundle(b_sci)
        store.save_bundle(b_tel)

        sim = Simulator(mock_contact_manager, store, queue, clock)
        sim.tick(2)

        assert queue.size() == 1
        assert store.load_bundle("tel-1").status == BundleStatus.STORED
        assert store.load_bundle("sci-1").status == BundleStatus.QUEUED