import pytest

from aether_benchmarks import BenchmarkCaseSpec, BenchmarkPack, BenchmarkRunner
from aether_routing_context import RoutingContextBuilder
from aether_routing_scoring import ProbabilisticScorer
from aether_scenarios import ScenarioGenerator, ScenarioSpec
from aether_security_routing import SecurityAwareRoutingEngine
from aether_security_signals import SecuritySignalBuilder


def create_base_spec(name="test_scene", seed=42) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_name=name,
        master_seed=seed,
        node_count=3,
        link_count=3,
        time_horizon=5,
        include_adversarial_trace=True,
        jamming_probability=0.5,
        malicious_drop_probability=0.2,
    )


def run_test_pack(pack: BenchmarkPack):
    runner = BenchmarkRunner()
    return runner.run_pack(
        pack,
        ScenarioGenerator(),
        RoutingContextBuilder(),
        ProbabilisticScorer(),
        SecuritySignalBuilder(),
        SecurityAwareRoutingEngine(),
    )


def test_benchmark_case_validation() -> None:
    spec = create_base_spec()

    with pytest.raises(ValueError, match="case_id must be a non-empty string"):
        BenchmarkCaseSpec("   ", "desc", spec, "N1", "N2", 1)

    with pytest.raises(ValueError, match="source_node_id must be a non-empty string"):
        BenchmarkCaseSpec("C1", "desc", spec, "", "N2", 1)

    with pytest.raises(ValueError, match="destination_node_id must be a non-empty string"):
        BenchmarkCaseSpec("C1", "desc", spec, "N1", "", 1)

    with pytest.raises(ValueError, match="time_index cannot be negative"):
        BenchmarkCaseSpec("C1", "desc", spec, "N1", "N2", -1)


def test_pack_name_validation() -> None:
    spec = create_base_spec()
    case = BenchmarkCaseSpec("C1", "desc", spec, "N1", "N2", 1)

    with pytest.raises(ValueError, match="pack_name must be a non-empty string"):
        BenchmarkPack("   ", [case], {})


def test_duplicate_case_id_validation() -> None:
    spec = create_base_spec()
    case_1 = BenchmarkCaseSpec("C1", "desc1", spec, "N1", "N2", 1)
    case_2 = BenchmarkCaseSpec("C1", "desc2", spec, "N1", "N2", 1)

    with pytest.raises(ValueError, match="Duplicate case_id found"):
        BenchmarkPack("Pack1", [case_1, case_2], {})


def test_stable_case_ordering() -> None:
    spec = create_base_spec()
    case_z = BenchmarkCaseSpec("case_Z", "desc", spec, "N1", "N2", 1)
    case_a = BenchmarkCaseSpec("case_A", "desc", spec, "N1", "N2", 1)

    pack = BenchmarkPack("Pack1", [case_z, case_a], {})
    result = run_test_pack(pack)

    assert result.case_results[0].case_id == "case_A"
    assert result.case_results[1].case_id == "case_Z"

    exported = result.to_dict()
    assert exported["case_results"][0]["case_id"] == "case_A"
    assert exported["case_results"][1]["case_id"] == "case_Z"


def test_deterministic_benchmark_execution() -> None:
    spec = create_base_spec()
    case = BenchmarkCaseSpec(
        "C1",
        "desc",
        spec,
        "N1",
        "N2",
        1,
        candidate_link_ids=["L1", "L2"],
    )
    pack = BenchmarkPack("Pack1", [case], {})

    result_1 = run_test_pack(pack)
    result_2 = run_test_pack(pack)

    assert result_1.to_dict() == result_2.to_dict()


def test_optional_candidate_links_behavior() -> None:
    spec = create_base_spec()
    case = BenchmarkCaseSpec(
        "C1",
        "desc",
        spec,
        "N1",
        "N2",
        1,
        candidate_link_ids=None,
    )
    pack = BenchmarkPack("Pack1", [case], {})

    result = run_test_pack(pack)
    case_result = result.case_results[0]

    assert case_result.routing_context.candidate_link_ids == ["L1", "L2", "L3"]


def test_summary_correctness() -> None:
    hostile_spec = ScenarioSpec(
        scenario_name="hostile",
        master_seed=99,
        node_count=3,
        link_count=2,
        time_horizon=2,
        include_adversarial_trace=True,
        jamming_probability=1.0,
        malicious_drop_probability=1.0,
        node_compromise_probability=1.0,
    )
    case_1 = BenchmarkCaseSpec("C1", "hostile", hostile_spec, "N1", "N2", 1)

    clean_spec = ScenarioSpec(
        scenario_name="clean",
        master_seed=1,
        node_count=3,
        link_count=2,
        time_horizon=2,
    )
    case_2 = BenchmarkCaseSpec("C2", "clean", clean_spec, "N1", "N2", 1)

    pack = BenchmarkPack("MixedPack", [case_1, case_2], {})
    result = run_test_pack(pack)
    summary = result.summary

    assert summary["case_count"] == 2
    assert summary["avoid_link_total"] == 2
    assert summary["high_severity_link_total"] == 2
    assert summary["compromised_node_total"] == 3
    assert summary["preferred_link_total"] == 2
    assert summary["allowed_link_total"] == 0


def test_export_mutation_safety() -> None:
    spec = create_base_spec()
    case = BenchmarkCaseSpec("C1", "desc", spec, "N1", "N2", 1)
    pack = BenchmarkPack("Pack1", [case], {})

    result = run_test_pack(pack)
    exported = result.to_dict()

    exported["metadata"]["runner_name"] = "BROKEN"
    exported["summary"]["case_count"] = 999
    exported["case_results"][0]["metadata"]["description"] = "HACKED"

    exported_again = result.to_dict()
    assert exported_again["metadata"]["runner_name"] == "BenchmarkRunner"
    assert exported_again["summary"]["case_count"] == 1
    assert exported_again["case_results"][0]["metadata"]["description"] == "desc"