import pytest
import tempfile, json
from pathlib import Path

from store.store import DTNStore
from bundle_queue.priority_queue import StrictPriorityQueue
from router.bundle import Bundle, BundleStatus
from router.contact_manager import Contact
from sim.simulator import create_default_simulator
from link.capacity_manager import ContactWindowCapacityManager
from metrics.network_metrics import (
    compute_store_depth_final,
    compute_queue_depth_final,
    compute_link_utilization
)


def test_compute_store_depth_final():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DTNStore(tmpdir)
        assert compute_store_depth_final(store) == 0
        
        bundle = Bundle("test-1", "telemetry", "A", "B", 10, 0, 100, 50, "ref")
        store.save_bundle(bundle)
        
        assert compute_store_depth_final(store) == 1


def test_compute_queue_depth_final():
    lunar_q = StrictPriorityQueue()
    relay_q = StrictPriorityQueue()
    
    bundle1 = Bundle("test-1", "telemetry", "A", "B", 10, 0, 100, 50, "ref")
    bundle2 = Bundle("test-2", "science", "A", "B", 5, 0, 100, 50, "ref")
    
    lunar_q.enqueue(bundle1)
    lunar_q.enqueue(bundle2)
    relay_q.enqueue(bundle1)
    
    depths = compute_queue_depth_final(lunar_q, relay_q)
    assert depths["lunar"] == 2
    assert depths["relay"] == 1


def test_compute_link_utilization():
    manager = ContactWindowCapacityManager()
    
    unlimited = Contact("A", "B", 0, 10, 0, 1000, capacity_bundles=None)
    zero_cap = Contact("A", "C", 0, 10, 0, 1000, capacity_bundles=0)
    finite_1 = Contact("B", "C", 5, 15, 0, 1000, capacity_bundles=4)
    finite_2 = Contact("C", "D", 10, 20, 0, 1000, capacity_bundles=2)
    
    contacts = [unlimited, zero_cap, finite_1, finite_2]
    
    # Simulate usage
    manager.record_forward(finite_1) # used 1/4 (0.25)
    
    manager.record_forward(finite_2)
    manager.record_forward(finite_2) # used 2/2 (1.0)
    
    report = compute_link_utilization(contacts, manager)
    
    # Unlimited should be omitted entirely
    assert len(report) == 3
    
    # Find specific reports
    zero_rep = next(r for r in report if r["target"] == "C" and r["source"] == "A")
    f1_rep = next(r for r in report if r["target"] == "C" and r["source"] == "B")
    f2_rep = next(r for r in report if r["target"] == "D" and r["source"] == "C")
    
    # Assert zero capacity behavior
    assert zero_rep["capacity_bundles"] == 0
    assert zero_rep["used_bundles"] == 0
    assert zero_rep["remaining_bundles"] == 0
    assert zero_rep["utilization_ratio"] is None
    
    # Assert finite partial utilization
    assert f1_rep["capacity_bundles"] == 4
    assert f1_rep["used_bundles"] == 1
    assert f1_rep["remaining_bundles"] == 3
    assert f1_rep["utilization_ratio"] == 0.25
    
    # Assert finite full utilization
    assert f2_rep["capacity_bundles"] == 2
    assert f2_rep["used_bundles"] == 2
    assert f2_rep["remaining_bundles"] == 0
    assert f2_rep["utilization_ratio"] == 1.0
    
def test_final_report_contains_network_metrics():
    plan = {
        "simulation_duration_sec": 5,
        "contacts": []
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = plan_file.name

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(plan_path=plan_path, store_dir=tmpstore)
            report = sim.run()

            assert "network_metrics" in report
            assert "store_depth_final" in report["network_metrics"]
            assert "queue_depth_final" in report["network_metrics"]
            assert "link_utilization" in report["network_metrics"]
    finally:
        import os
        os.unlink(plan_path)