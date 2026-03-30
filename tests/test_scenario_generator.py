import pytest

from aether_scenarios import ScenarioGenerator, ScenarioSpec


def test_validation_bounds() -> None:
    with pytest.raises(ValueError, match="scenario_name must be a non-empty string"):
        ScenarioSpec(
            scenario_name="  ",
            master_seed=42,
            node_count=5,
            link_count=5,
            time_horizon=5,
        )

    with pytest.raises(ValueError, match="node_count cannot be negative"):
        ScenarioSpec("test", 42, -1, 5, 5)

    with pytest.raises(ValueError, match="link_count cannot be negative"):
        ScenarioSpec("test", 42, 5, -1, 5)

    with pytest.raises(ValueError, match="time_horizon cannot be negative"):
        ScenarioSpec("test", 42, 5, 5, -1)


def test_id_generation_correctness() -> None:
    spec = ScenarioSpec("test", 42, node_count=2, link_count=3, time_horizon=4)
    scenario = ScenarioGenerator().generate(spec)

    assert scenario.node_ids == ["N1", "N2"]
    assert scenario.link_ids == ["L1", "L2", "L3"]
    assert scenario.time_indices == [0, 1, 2, 3]


def test_deterministic_scenario_generation() -> None:
    spec = ScenarioSpec(
        scenario_name="stable_test",
        master_seed=999,
        node_count=3,
        link_count=4,
        time_horizon=10,
        include_reliability_trace=True,
        include_adversarial_trace=True,
        loss_probability=0.5,
        jamming_probability=0.5,
    )

    scenario_a = ScenarioGenerator().generate(spec)
    scenario_b = ScenarioGenerator().generate(spec)

    assert scenario_a.to_dict() == scenario_b.to_dict()


def test_optional_trace_inclusion() -> None:
    generator = ScenarioGenerator()

    spec_none = ScenarioSpec("t1", 1, 1, 1, 1, False, False)
    scenario_none = generator.generate(spec_none)
    assert scenario_none.reliability_trace is None
    assert scenario_none.adversarial_trace is None

    spec_rel = ScenarioSpec("t2", 1, 1, 1, 1, True, False)
    scenario_rel = generator.generate(spec_rel)
    assert scenario_rel.reliability_trace is not None
    assert scenario_rel.adversarial_trace is None

    spec_adv = ScenarioSpec("t3", 1, 1, 1, 1, False, True)
    scenario_adv = generator.generate(spec_adv)
    assert scenario_adv.reliability_trace is None
    assert scenario_adv.adversarial_trace is not None

    spec_both = ScenarioSpec("t4", 1, 1, 1, 1, True, True)
    scenario_both = generator.generate(spec_both)
    assert scenario_both.reliability_trace is not None
    assert scenario_both.adversarial_trace is not None


def test_stable_export_structure_and_metadata() -> None:
    spec = ScenarioSpec(
        "meta_test",
        123,
        2,
        2,
        2,
        include_reliability_trace=True,
    )
    scenario = ScenarioGenerator().generate(spec)

    doc = scenario.to_dict()

    assert doc["type"] == "scenario_artifact"
    assert doc["version"] == "1.0"
    assert doc["scenario_name"] == "meta_test"
    assert doc["master_seed"] == 123

    assert "metadata" in doc
    assert doc["metadata"]["generator_name"] == "ScenarioGenerator"
    assert doc["metadata"]["generator_version"] == "1.0"
    assert doc["metadata"]["has_reliability_trace"] is True
    assert doc["metadata"]["has_adversarial_trace"] is False
    assert doc["metadata"]["stream_names"]["reliability"] == (
        "scenario::meta_test::reliability"
    )
    assert doc["metadata"]["stream_names"]["adversarial"] is None

    assert doc["topology"]["node_count"] == 2
    assert doc["topology"]["link_count"] == 2
    assert doc["topology"]["time_horizon"] == 2
    assert doc["reliability_trace"] is not None
    assert doc["adversarial_trace"] is None


def test_export_does_not_leak_internal_mutable_references() -> None:
    spec = ScenarioSpec(
        scenario_name="copy_test",
        master_seed=77,
        node_count=2,
        link_count=2,
        time_horizon=3,
        include_reliability_trace=False,
        include_adversarial_trace=False,
    )
    scenario = ScenarioGenerator().generate(spec)

    exported = scenario.to_dict()
    exported["metadata"]["generator_name"] = "Mutated"
    exported["topology"]["node_ids"][0] = "BROKEN"

    exported_again = scenario.to_dict()

    assert exported_again["metadata"]["generator_name"] == "ScenarioGenerator"
    assert exported_again["topology"]["node_ids"][0] == "N1"