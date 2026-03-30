from aether_random import RandomManager
from aether_reliability import (
    DelayEvent,
    DegradationEvent,
    LinkReliabilityTrace,
    LossEvent,
    ReliabilityTraceGenerator,
)


def test_trace_lookup_defaults() -> None:
    trace = LinkReliabilityTrace()

    assert trace.should_drop("link_A", 10) is False
    assert trace.get_extra_delay_ms("link_A", 10) == 0
    assert trace.is_degraded("link_A", 10) is False


def test_trace_stores_and_retrieves_separate_event_types() -> None:
    trace = LinkReliabilityTrace()

    trace.add_loss_event(LossEvent(link_id="link_A", time_index=5, drop=True))
    trace.add_delay_event(
        DelayEvent(link_id="link_A", time_index=5, extra_delay_ms=100)
    )
    trace.add_degradation_event(
        DegradationEvent(link_id="link_A", time_index=5, degraded=True)
    )

    assert trace.should_drop("link_A", 5) is True
    assert trace.get_extra_delay_ms("link_A", 5) == 100
    assert trace.is_degraded("link_A", 5) is True

    assert trace.should_drop("link_A", 6) is False
    assert trace.get_extra_delay_ms("link_A", 6) == 0
    assert trace.is_degraded("link_A", 6) is False


def test_trace_export_stability_and_numeric_sorting() -> None:
    trace = LinkReliabilityTrace()

    trace.add_loss_event(LossEvent(link_id="L1", time_index=10, drop=True))
    trace.add_loss_event(LossEvent(link_id="L1", time_index=2, drop=True))
    trace.add_delay_event(DelayEvent(link_id="A1", time_index=3, extra_delay_ms=50))
    trace.add_degradation_event(
        DegradationEvent(link_id="Z9", time_index=1, degraded=True)
    )

    doc = trace.to_dict()

    assert doc["type"] == "link_reliability_trace"
    assert doc["version"] == "1.0"
    assert doc["loss_event_count"] == 2
    assert doc["delay_event_count"] == 1
    assert doc["degradation_event_count"] == 1

    assert doc["loss_events"][0]["time_index"] == 2
    assert doc["loss_events"][1]["time_index"] == 10


def test_deterministic_generation() -> None:
    rm1 = RandomManager(42)
    rm2 = RandomManager(42)

    gen1 = ReliabilityTraceGenerator(rm1)
    gen2 = ReliabilityTraceGenerator(rm2)

    links = ["L1", "L2"]
    times = [0, 1, 2, 3]

    trace1 = gen1.generate_for_links(
        links,
        times,
        loss_probability=0.5,
        max_extra_delay_ms=10,
        degradation_probability=0.25,
        stream_name="same_run",
    )
    trace2 = gen2.generate_for_links(
        links,
        times,
        loss_probability=0.5,
        max_extra_delay_ms=10,
        degradation_probability=0.25,
        stream_name="same_run",
    )

    assert trace1.to_dict() == trace2.to_dict()


def test_stream_name_derives_distinct_seed() -> None:
    rm = RandomManager(99)

    seed_a = rm.get_stream_seed("reliability_trace::run_A")
    seed_b = rm.get_stream_seed("reliability_trace::run_B")

    assert seed_a != seed_b


def test_different_stream_names_produce_different_traces() -> None:
    rm = RandomManager(99)
    gen = ReliabilityTraceGenerator(rm)

    links = ["L1", "L2", "L3"]
    times = list(range(20))

    trace_a = gen.generate_for_links(
        links,
        times,
        loss_probability=0.35,
        max_extra_delay_ms=7,
        degradation_probability=0.4,
        stream_name="run_A",
    )
    trace_b = gen.generate_for_links(
        links,
        times,
        loss_probability=0.35,
        max_extra_delay_ms=7,
        degradation_probability=0.4,
        stream_name="run_B",
    )

    assert trace_a.to_dict() != trace_b.to_dict()


def test_delay_bounds_and_boolean_semantics() -> None:
    rm = RandomManager(123)
    gen = ReliabilityTraceGenerator(rm)

    max_delay = 45
    trace = gen.generate_for_links(
        ["L1"],
        list(range(100)),
        loss_probability=0.5,
        max_extra_delay_ms=max_delay,
        degradation_probability=0.5,
    )

    doc = trace.to_dict()

    for event in doc["loss_events"]:
        assert isinstance(event["drop"], bool)

    for event in doc["degradation_events"]:
        assert isinstance(event["degraded"], bool)

    for event in doc["delay_events"]:
        assert 1 <= event["extra_delay_ms"] <= max_delay


def test_invalid_probabilities_raise_value_error() -> None:
    rm = RandomManager(1)
    gen = ReliabilityTraceGenerator(rm)

    try:
        gen.generate_for_links(
            ["L1"],
            [0, 1],
            loss_probability=-0.1,
        )
        assert False, "Expected ValueError for negative loss_probability"
    except ValueError:
        pass

    try:
        gen.generate_for_links(
            ["L1"],
            [0, 1],
            degradation_probability=1.1,
        )
        assert False, "Expected ValueError for degradation_probability > 1.0"
    except ValueError:
        pass


def test_negative_max_extra_delay_raises_value_error() -> None:
    rm = RandomManager(1)
    gen = ReliabilityTraceGenerator(rm)

    try:
        gen.generate_for_links(
            ["L1"],
            [0, 1],
            max_extra_delay_ms=-1,
        )
        assert False, "Expected ValueError for negative max_extra_delay_ms"
    except ValueError:
        pass