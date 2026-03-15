import json
import tempfile
from pathlib import Path

from sim.simulator import create_default_simulator
from node.node_runtime import NodeRuntime

def test_simulator_uses_node_runtimes():
    plan = {
        "simulation_duration_sec": 10,
        "contacts": []
    }
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = plan_file.name

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(
                plan_path=plan_path,
                store_dir=tmpstore,
                scenario_name="node_test"
            )
            
            # Assert that nodes are explicitly tracked as NodeRuntime objects
            assert "lunar-node" in sim.nodes
            assert isinstance(sim.nodes["lunar-node"], NodeRuntime)
            assert sim.nodes["lunar-node"].role == "source"
            
            # Assert backward compatibility property works
            queues = sim.node_queues
            assert "lunar-node" in queues
            assert queues["lunar-node"] is sim.lunar_queue

    finally:
        Path(plan_path).unlink()