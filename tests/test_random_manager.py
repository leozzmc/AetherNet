from aether_random import RandomManager, derive_stream_seed


def test_derive_stream_seed_is_deterministic() -> None:
    assert derive_stream_seed(42, "alpha") == derive_stream_seed(42, "alpha")


def test_derive_stream_seed_differs_across_stream_names() -> None:
    assert derive_stream_seed(42, "alpha") != derive_stream_seed(42, "beta")


def test_get_stream_is_deterministic_across_managers() -> None:
    rm1 = RandomManager(42)
    rm2 = RandomManager(42)

    s1 = rm1.get_stream("stream_a")
    s2 = rm2.get_stream("stream_a")

    values1 = [s1.random() for _ in range(10)]
    values2 = [s2.random() for _ in range(10)]

    assert values1 == values2


def test_stream_independence() -> None:
    rm = RandomManager(42)

    a = rm.get_stream("stream_a").random()
    b = rm.get_stream("stream_b").random()

    assert a != b


def test_get_stream_returns_cached_stateful_stream() -> None:
    rm = RandomManager(42)

    s1 = rm.get_stream("stream_x")
    s2 = rm.get_stream("stream_x")

    assert s1 is s2


def test_create_stream_returns_fresh_stream_each_time() -> None:
    rm = RandomManager(42)

    s1 = rm.create_stream("stream_x")
    s2 = rm.create_stream("stream_x")

    assert s1 is not s2

    values1 = [s1.random() for _ in range(10)]
    values2 = [s2.random() for _ in range(10)]

    assert values1 == values2


def test_repeatability_with_fresh_streams() -> None:
    rm = RandomManager(999)

    stream1 = rm.create_stream("test_stream")
    values1 = [stream1.random() for _ in range(10)]

    stream2 = rm.create_stream("test_stream")
    values2 = [stream2.random() for _ in range(10)]

    assert values1 == values2


def test_seed_registry_export_records_streams() -> None:
    rm = RandomManager(12345)

    rm.get_stream("alpha")
    rm.create_stream("beta")

    registry_data = rm.registry.export()

    assert "alpha" in registry_data
    assert "beta" in registry_data
    assert registry_data["alpha"] != registry_data["beta"]


def test_seed_registry_export_returns_copy() -> None:
    rm = RandomManager(12345)
    rm.get_stream("alpha")

    exported = rm.registry.export()
    exported["alpha"] = 0

    assert rm.registry.export()["alpha"] != 0


def test_advancing_one_stream_does_not_affect_another() -> None:
    rm = RandomManager(42)

    baseline = RandomManager(42)
    expected_b_first = baseline.get_stream("stream_b").random()

    stream_a = rm.get_stream("stream_a")
    for _ in range(5):
        stream_a.random()

    actual_b_first = rm.get_stream("stream_b").random()
    assert actual_b_first == expected_b_first


def test_get_stream_seed_matches_registered_seed() -> None:
    rm = RandomManager(77)

    rm.get_stream("gamma")
    exported = rm.registry.export()

    assert exported["gamma"] == rm.get_stream_seed("gamma")