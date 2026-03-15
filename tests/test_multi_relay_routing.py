import json
import pytest
import tempfile
from pathlib import Path

from sim.simulator import Simulator
from sim.event_loop import SimulationClock
from store.store import DTNStore
from bundle_queue.priority_queue import StrictPriorityQueue
from router.contact_manager import ContactManager
from router.app import AetherRouter
from routing.routing_table import RoutingTable
from router.bundle import Bundle
from metrics.exporter import MetricsCollector


def test_multi_relay_chain_end_to_end():
    # 1. Define Contact Plan for a 3-hop journey
    plan = {
        "simulation_duration_sec": 40,
        "contacts": [
            {"source": "lunar-node", "target": "relay-a", "start_time": 0, "end_time": 10},
            {"source": "relay-a", "target": "relay-b", "start_time": 10, "end_time": 20},
            {"source": "relay-b", "target": "ground-station", "start_time": 20, "end_time": 30}
        ]
    }
    
    # 2. Define Explicit Routing Table
    rt = RoutingTable({
        "lunar-node": {"ground-station": "relay-a"},
        "relay-a": {"ground-station": "relay-b"},
        "relay-b": {"ground-station": "ground-station"}
    })

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = plan_file.name

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            # 3. Setup Simulator Infrastructure
            cm = ContactManager(str(plan_path))
            router = AetherRouter(contact_manager=cm, routing_table=rt)
            store = DTNStore(tmpstore)
            clock = SimulationClock(start_time=0, end_time=40, tick_size=1)
            metrics = MetricsCollector()
            
            lunar_queue = StrictPriorityQueue()
            relay_queue = StrictPriorityQueue() # Placeholder leo-relay (unused in this scenario)
            relay_a_queue = StrictPriorityQueue()
            relay_b_queue = StrictPriorityQueue()
            
            # Inject Test Bundle
            b1 = Bundle(
                id="tel-001", type="telemetry", source="lunar-node", destination="ground-station",
                priority=100, created_at=0, ttl_sec=3600, size_bytes=100, payload_ref="demo"
            )
            lunar_queue.enqueue(b1)
            store.save_bundle(b1)

            # 4. Initialize Simulator with Multi-Relay support
            sim = Simulator(
                router_or_contact_manager=router,
                store=store,
                lunar_queue=lunar_queue,
                relay_queue_or_clock=relay_queue,
                clock=clock,
                metrics=metrics,
                scenario_name="multi_relay_chain",
                injected_bundle_ids=["tel-001"],
                extra_queues={"relay-a": relay_a_queue, "relay-b": relay_b_queue}
            )

            report = sim.run()

            # 5. Assert End-to-End Success
            delivered = report.get("delivered_bundle_ids", [])
            assert "tel-001" in delivered, "Bundle failed to traverse the multi-relay chain"
            
            # 6. Assert Metrics reflect multi-hop journey
            forwarded = report.get("final_metrics", {}).get("bundles_forwarded_total", {})
            assert forwarded.get("telemetry", 0) == 3, "Bundle should have been forwarded exactly 3 times"

    finally:
        Path(plan_path).unlink()