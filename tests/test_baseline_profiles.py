import pytest

from sim.baseline_profiles import build_baseline_profile, list_baseline_profiles
from sim.experiment_harness import ExperimentCase, ExperimentHarness


def test_profile_list_is_deterministic():
    profiles = list_baseline_profiles()

    assert isinstance(profiles, list)
    assert len(profiles) == 3
    assert profiles == [
        "delivery_stress_baseline",
        "minimal_baseline",
        "routing_baseline",
    ]


def test_minimal_baseline_builds_valid_cases():
    cases = build_baseline_profile("minimal_baseline")

    assert len(cases) == 1
    assert isinstance(cases[0], ExperimentCase)
    assert cases[0].case_name == "minimal_baseline__default_multihop"
    assert cases[0].scenario_name == "default_multihop"
    assert cases[0].tick_size == 1


def test_routing_baseline_deterministic_ordering():
    cases_run_1 = build_baseline_profile("routing_baseline")
    cases_run_2 = build_baseline_profile("routing_baseline")

    assert len(cases_run_1) == 2

    assert [case.case_name for case in cases_run_1] == [
        case.case_name for case in cases_run_2
    ]
    assert [case.scenario_name for case in cases_run_1] == [
        case.scenario_name for case in cases_run_2
    ]
    assert [case.tick_size for case in cases_run_1] == [
        case.tick_size for case in cases_run_2
    ]

    assert cases_run_1[0].case_name == "routing_baseline__default_multihop__tick1"
    assert cases_run_1[1].case_name == "routing_baseline__default_multihop__tick5"
    assert cases_run_1[0].scenario_name == "default_multihop"
    assert cases_run_1[1].scenario_name == "default_multihop"
    assert cases_run_1[0].tick_size == 1
    assert cases_run_1[1].tick_size == 5


def test_delivery_stress_baseline_deterministic_ordering():
    cases_run_1 = build_baseline_profile("delivery_stress_baseline")
    cases_run_2 = build_baseline_profile("delivery_stress_baseline")

    assert len(cases_run_1) == 2

    assert [case.case_name for case in cases_run_1] == [
        case.case_name for case in cases_run_2
    ]
    assert [case.scenario_name for case in cases_run_1] == [
        case.scenario_name for case in cases_run_2
    ]

    assert cases_run_1[0].case_name == "delivery_stress__delayed_delivery"
    assert cases_run_1[0].scenario_name == "delayed_delivery"

    assert cases_run_1[1].case_name == "delivery_stress__expiry_before_contact"
    assert cases_run_1[1].scenario_name == "expiry_before_contact"


def test_unknown_profile_raises_value_error():
    with pytest.raises(ValueError) as excinfo:
        build_baseline_profile("non_existent_profile_123")

    assert "Unknown baseline profile: 'non_existent_profile_123'" in str(excinfo.value)
    assert "minimal_baseline" in str(excinfo.value)


def test_integration_with_experiment_harness():
    """
    Wave-61: Profiles must not just be structurally valid;
    they must actually be executable by the current experiment pipeline.
    """
    cases = build_baseline_profile("minimal_baseline")

    results = ExperimentHarness.run_experiments(cases)

    assert len(results) == 1
    assert results[0].case_name == "minimal_baseline__default_multihop"
    assert results[0].scenario_name == "default_multihop"
    assert hasattr(results[0], "delivery_ratio")
    assert hasattr(results[0], "store_bundle_ids_remaining")