import pytest

from aether_phase6_runtime.benchmarks import (
    RuntimeBenchmarkScenario,
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)


def test_scenario_validation_rejects_blank_id() -> None:
    with pytest.raises(ValueError, match="scenario_id must be a non-empty string"):
        RuntimeBenchmarkScenario("  ", ["L1"], [], [])


def test_default_scenarios_exist_and_are_deterministic() -> None:
    scenarios = default_runtime_benchmark_scenarios()
    
    assert len(scenarios) == 4
    ids = [s.scenario_id for s in scenarios]
    assert ids == ["clean", "degraded", "jammed", "mixed_risk"]
    
    # Determinism checks
    dict1 = scenarios[0].to_dict()
    dict2 = default_runtime_benchmark_scenarios()[0].to_dict()
    assert dict1 == dict2


def test_benchmark_suite_returns_result_for_every_scenario_x_mode() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    
    suite_result = runner.run_suite("test_suite_1", scenarios)
    
    # 4 scenarios * 3 modes = 12 results
    assert len(suite_result.results) == 12
    assert suite_result.suite_id == "test_suite_1"


def test_legacy_selects_highest_scoring_candidate_in_clean_scenario() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = [RuntimeBenchmarkScenario("clean", ["L1", "L2", "L3"], [], [])]
    
    suite_result = runner.run_suite("test_legacy_clean", scenarios)
    
    legacy_result = next(r for r in suite_result.results if r.routing_mode == "legacy")
    
    # L2 has the highest hardcoded metric score (90)
    assert legacy_result.selected_next_hop == "L2"
    assert legacy_result.decision_reason == "selected_scored_candidate"


def test_jammed_scenario_causes_phase6_modes_to_avoid_jammed_candidate() -> None:
    runner = RuntimeBenchmarkRunner()
    # L2 is the highest metric, but is jammed
    scenarios = [RuntimeBenchmarkScenario("jammed", ["L1", "L2", "L3"], [], ["L2"])]
    
    suite_result = runner.run_suite("test_jammed_avoid", scenarios)
    
    legacy = next(r for r in suite_result.results if r.routing_mode == "legacy")
    balanced = next(r for r in suite_result.results if r.routing_mode == "phase6_balanced")
    
    # Legacy blindly falls into the trap
    assert legacy.selected_next_hop == "L2"
    
    # Phase-6 intelligently routes around the threat
    assert balanced.selected_next_hop != "L2"
    assert balanced.selected_next_hop in ["L1", "L3"]
    assert balanced.candidate_count_after < balanced.candidate_count_before


def test_suite_summary_counts_modes_correctly() -> None:
    runner = RuntimeBenchmarkRunner()
    # Run 2 scenarios
    scenarios = default_runtime_benchmark_scenarios()[:2] 
    
    suite_result = runner.run_suite("test_summary", scenarios)
    
    # 2 scenarios * 3 modes = 6 total decisions
    assert suite_result.summary.total_decisions == 6
    assert suite_result.summary.mode_counts["legacy"] == 2
    assert suite_result.summary.mode_counts["phase6_balanced"] == 2
    assert suite_result.summary.mode_counts["phase6_adaptive"] == 2


def test_to_dict_mutation_safety() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = [RuntimeBenchmarkScenario("clean", ["L1"], [], [])]
    
    suite_result = runner.run_suite("test_mutation", scenarios)
    data = suite_result.to_dict()
    
    # Mutate JSON
    data["metadata"]["hacked"] = True
    data["results"][0]["routing_mode"] = "hacked"
    
    # Extract again
    safe_data = suite_result.to_dict()
    assert "hacked" not in safe_data["metadata"]
    assert safe_data["results"][0]["routing_mode"] != "hacked"


def test_deterministic_suite_output_across_two_runs() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    
    suite_1 = runner.run_suite("test_deterministic", scenarios)
    suite_2 = runner.run_suite("test_deterministic", scenarios)
    
    assert suite_1.to_dict() == suite_2.to_dict()