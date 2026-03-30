import pytest

from aether_random import RandomManager
from aether_adversarial import (
    AdversarialTrace,
    AdversarialTraceGenerator,
    DelayInjectionEvent,
    JammingEvent,
    MaliciousDropEvent,
    NodeCompromiseEvent,
)


def test_lookup_defaults() -> None:
    trace = AdversarialTrace()

    assert trace.is_jammed("link_A", 10) is False
    assert trace.should_maliciously_drop("link_A", 10) is False
    assert trace.get_injected_delay_ms("link_A", 10) == 0
    assert trace.is_node_compromised("node_X", 10) is False


def test_trace_stores_and_retrieves_all_event_types() -> None:
    trace = AdversarialTrace()

    trace.add_jamming_event(JammingEvent("L1", 5, jammed=True))
    trace.add_malicious_drop_event(MaliciousDropEvent("L1", 5, drop=True))
    trace.add_delay_injection_event(
        DelayInjectionEvent("L1", 5, injected_delay_ms=200)
    )
    trace.add_node_compromise_event(
        NodeCompromiseEvent("N1", 5, compromised=True)
    )

    assert trace.is_jammed("L1", 5) is True
    assert trace.should_maliciously_drop("L1", 5) is True
    assert trace.get_injected_delay_ms("L1", 5) == 200
    assert trace.is_node_compromised("N1", 5) is True

    assert trace.is_jammed("L1", 6) is False
    assert trace.is_node_compromised("N1", 6) is False


def test_stable_export_ordering() -> None:
    trace = AdversarialTrace()

    trace.add_node_compromise_event(
        NodeCompromiseEvent("N1", 10, compromised=True)
    )
    trace.add_node_compromise_event(
        NodeCompromiseEvent("N1", 2, compromised=True)
    )
    trace.add_jamming_event(JammingEvent("L2", 5, jammed=True))
    trace.add_jamming_event(JammingEvent("L1", 5, jammed=True))

    doc = trace.to_dict()

    assert doc["type"] == "adversarial_trace"
    assert doc["version"] == "1.0"
    assert doc["jamming_event_count"] == 2
    assert doc["node_compromise_event_count"] == 2

    assert doc["node_compromise_events"][0]["time_index"] == 2
    assert doc["node_compromise_events"][1]["time_index"] == 10
    assert doc["jamming_events"][0]["link_id"] == "L1"
    assert doc["jamming_events"][1]["link_id"] == "L2"


def test_deterministic_generation() -> None:
    rm1 = RandomManager(42)
    rm2 = RandomManager(42)

    gen1 = AdversarialTraceGenerator(rm1)
    gen2 = AdversarialTraceGenerator(rm2)

    links = ["L1", "L2"]
    nodes = ["N1"]
    times = [0, 1, 2]

    trace1 = gen1.generate(
        links,
        nodes,
        times,
        jamming_probability=0.5,
        malicious_drop_probability=0.5,
        max_injected_delay_ms=50,
        node_compromise_probability=0.5,
        stream_name="test_run",
    )
    trace2 = gen2.generate(
        links,
        nodes,
        times,
        jamming_probability=0.5,
        malicious_drop_probability=0.5,
        max_injected_delay_ms=50,
        node_compromise_probability=0.5,
        stream_name="test_run",
    )

    assert trace1.to_dict() == trace2.to_dict()


def test_distinct_stream_seeds_are_primary_independence_check() -> None:
    rm = RandomManager(99)

    seed_a = rm.get_stream_seed("adversarial_trace::run_A")
    seed_b = rm.get_stream_seed("adversarial_trace::run_B")

    assert seed_a != seed_b


def test_different_stream_names_produce_different_traces_as_secondary_check() -> None:
    rm = RandomManager(99)
    gen = AdversarialTraceGenerator(rm)

    links = ["L1", "L2", "L3"]
    nodes = ["N1", "N2"]
    times = list(range(20))

    trace_a = gen.generate(
        links,
        nodes,
        times,
        jamming_probability=0.4,
        node_compromise_probability=0.4,
        stream_name="run_A",
    )
    trace_b = gen.generate(
        links,
        nodes,
        times,
        jamming_probability=0.4,
        node_compromise_probability=0.4,
        stream_name="run_B",
    )

    assert trace_a.to_dict() != trace_b.to_dict()


def test_delay_bounds_and_boolean_semantics() -> None:
    rm = RandomManager(123)
    gen = AdversarialTraceGenerator(rm)

    max_delay = 300
    trace = gen.generate(
        ["L1"],
        ["N1"],
        list(range(50)),
        jamming_probability=0.5,
        malicious_drop_probability=0.5,
        max_injected_delay_ms=max_delay,
        node_compromise_probability=0.5,
    )

    doc = trace.to_dict()

    for event in doc["jamming_events"]:
        assert isinstance(event["jammed"], bool)

    for event in doc["malicious_drop_events"]:
        assert isinstance(event["drop"], bool)

    for event in doc["node_compromise_events"]:
        assert isinstance(event["compromised"], bool)

    for event in doc["delay_injection_events"]:
        assert 1 <= event["injected_delay_ms"] <= max_delay


def test_input_validation() -> None:
    rm = RandomManager(1)
    gen = AdversarialTraceGenerator(rm)

    with pytest.raises(
        ValueError,
        match="jamming_probability must be between 0.0 and 1.0",
    ):
        gen.generate(["L1"], ["N1"], [0], jamming_probability=1.5)

    with pytest.raises(
        ValueError,
        match="malicious_drop_probability must be between 0.0 and 1.0",
    ):
        gen.generate(["L1"], ["N1"], [0], malicious_drop_probability=-0.2)

    with pytest.raises(
        ValueError,
        match="node_compromise_probability must be between 0.0 and 1.0",
    ):
        gen.generate(["L1"], ["N1"], [0], node_compromise_probability=-0.1)

    with pytest.raises(
        ValueError,
        match="max_injected_delay_ms must be >= 0",
    ):
        gen.generate(["L1"], ["N1"], [0], max_injected_delay_ms=-50)