import pytest

from aether_phase6_runtime.benchmarks import (
    RuntimeBenchmarkResult,
    RuntimeBenchmarkSuiteResult,
)
from aether_phase6_runtime.report import BenchmarkReportBuilder
from aether_phase6_runtime.simulation_metrics import SimulationRoutingMetricsSummary


def create_mock_suite_result() -> RuntimeBenchmarkSuiteResult:
    results = [
        RuntimeBenchmarkResult("jammed", "phase6_balanced", "L1", "reason", 3, 2, False, {}),
        RuntimeBenchmarkResult("clean", "legacy", "L2", "reason", 3, 3, False, {}),
        RuntimeBenchmarkResult("jammed", "phase6_adaptive", "L1", "reason", 3, 2, False, {}),
        RuntimeBenchmarkResult("clean", "phase6_adaptive", "L2", "reason", 3, 3, False, {}),
        RuntimeBenchmarkResult("clean", "phase6_balanced", "L2", "reason", 3, 3, False, {}),
        RuntimeBenchmarkResult("jammed", "legacy", "L2", "reason", 3, 3, False, {}),
    ]

    summary = SimulationRoutingMetricsSummary(
        total_decisions=6,
        mode_counts={
            "legacy": 2,
            "phase6_balanced": 2,
            "phase6_adaptive": 2,
        },
        filtered_all_count=0,
        selected_next_hop_counts={
            "L2": 4,
            "L1": 2,
        },
    )

    return RuntimeBenchmarkSuiteResult(
        suite_id="test_suite_1",
        results=results,
        summary=summary,
        metadata={},
    )


@pytest.fixture
def builder() -> BenchmarkReportBuilder:
    return BenchmarkReportBuilder()


def test_report_text_contains_required_sections(
    builder: BenchmarkReportBuilder,
) -> None:
    report = builder.build(create_mock_suite_result())

    assert "=== Phase-6 Runtime Benchmark Report ===" in report.text
    assert "Suite: test_suite_1" in report.text
    assert "[Summary]" in report.text
    assert "Total Decisions: 6" in report.text
    assert "Mode Counts:" in report.text
    assert "- legacy: 2" in report.text
    assert "- phase6_balanced: 2" in report.text
    assert "- phase6_adaptive: 2" in report.text
    assert "Filtered-All Count: 0" in report.text
    assert "[Per Scenario]" in report.text
    assert "Scenario: clean" in report.text
    assert "Scenario: jammed" in report.text
    assert "- legacy -> L2" in report.text
    assert "- balanced -> L2" in report.text
    assert "- adaptive -> L2" in report.text


def test_structured_output_schema_correctness(
    builder: BenchmarkReportBuilder,
) -> None:
    report = builder.build(create_mock_suite_result())

    structured = report.structured

    assert structured["suite_id"] == "test_suite_1"
    assert "summary" in structured
    assert structured["summary"]["total_decisions"] == 6
    assert len(structured["scenarios"]) == 2

    clean = next(
        scenario for scenario in structured["scenarios"]
        if scenario["scenario_id"] == "clean"
    )

    assert len(clean["results"]) == 3
    assert clean["results"][0]["routing_mode"] == "legacy"
    assert clean["results"][1]["routing_mode"] == "phase6_balanced"
    assert clean["results"][2]["routing_mode"] == "phase6_adaptive"


def test_scenario_grouping_is_deterministic(
    builder: BenchmarkReportBuilder,
) -> None:
    report = builder.build(create_mock_suite_result())

    scenario_ids = [
        scenario["scenario_id"]
        for scenario in report.structured["scenarios"]
    ]

    assert scenario_ids == ["clean", "jammed"]


def test_deterministic_output_across_runs(
    builder: BenchmarkReportBuilder,
) -> None:
    suite_result = create_mock_suite_result()

    report_a = builder.build(suite_result)
    report_b = builder.build(suite_result)

    assert report_a.text == report_b.text
    assert report_a.structured == report_b.structured
    assert report_a.to_dict() == report_b.to_dict()


def test_mutation_safety(
    builder: BenchmarkReportBuilder,
) -> None:
    report = builder.build(create_mock_suite_result())

    exported = report.to_dict()
    exported["structured"]["scenarios"][0]["scenario_id"] = "HACKED"

    exported_again = report.to_dict()

    assert exported_again["structured"]["scenarios"][0]["scenario_id"] != "HACKED"


def test_to_dict_schema_is_stable(
    builder: BenchmarkReportBuilder,
) -> None:
    report = builder.build(create_mock_suite_result())
    data = report.to_dict()

    assert data["type"] == "benchmark_report"
    assert data["version"] == "1.0"
    assert data["suite_id"] == "test_suite_1"
    assert "text" in data
    assert "structured" in data


def test_empty_suite_result_handling(
    builder: BenchmarkReportBuilder,
) -> None:
    empty_summary = SimulationRoutingMetricsSummary(
        total_decisions=0,
        mode_counts={},
        filtered_all_count=0,
        selected_next_hop_counts={},
    )
    empty_suite = RuntimeBenchmarkSuiteResult(
        suite_id="empty_suite",
        results=[],
        summary=empty_summary,
        metadata={},
    )

    report = builder.build(empty_suite)

    assert "Total Decisions: 0" in report.text
    assert "Filtered-All Count: 0" in report.text
    assert report.structured["scenarios"] == []