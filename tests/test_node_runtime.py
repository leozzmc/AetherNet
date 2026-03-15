import pytest
from node.node_runtime import NodeRuntime
from bundle_queue.priority_queue import StrictPriorityQueue

def test_node_runtime_initialization():
    q = StrictPriorityQueue()
    node = NodeRuntime(node_id="test-node", queue=q, role="relay")
    
    assert node.node_id == "test-node"
    assert node.queue is q
    assert node.role == "relay"

def test_node_runtime_optional_role():
    q = StrictPriorityQueue()
    node = NodeRuntime(node_id="simple-node", queue=q)
    
    assert node.node_id == "simple-node"
    assert node.role is None