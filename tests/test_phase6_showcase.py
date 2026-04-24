import pytest

from aether_phase6_runtime.comparison import PolicyComparisonResult
from aether_phase6_runtime.showcase import PolicyShowcaseBuilder


@pytest.fixture
def builder() -> PolicyShowcaseBuilder:
    return PolicyShowcaseBuilder()


def create_mock_comparison_result(
    case_id: str = "test-case",
    baseline: list[str] | None = None,
    conservative: list[str] | None = None,
    balanced: list[str] | None = None,
    aggressive: list[str] | None = None,
) -> PolicyComparisonResult:
    return PolicyComparisonResult(
        case_id=case_id,
        baseline_candidates=baseline if baseline is not None else ["L1", "L2"],
        conservative_candidates=conservative if conservative is not None else ["L1"],
        balanced_candidates=balanced if balanced is not None else ["L1", "L2"],
        aggressive_candidates=aggressive if aggressive is not None else ["L2", "L1"],
        metadata={},
    )


def test_showcase_generation_is_deterministic(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result()

    report_a = builder.build(result)
    report_b = builder.build(result)

    assert report_a.text == report_b.text
    assert report_a.to_dict() == report_b.to_dict()


def test_all_required_sections_exist(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result()
    report = builder.build(result)

    assert "=== Phase-6 Runtime Policy Showcase ===" in report.text
    assert "[Candidate Outputs]" in report.text
    assert "[Policy Differences]" in report.text
    assert "[Interpretation]" in report.text


def test_empty_candidate_lists_render_as_none(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result(
        baseline=[],
        conservative=[],
        balanced=[],
        aggressive=[],
    )

    report = builder.build(result)

    assert "Baseline: none" in report.text
    assert "Conservative: none" in report.text
    assert "Balanced: none" in report.text
    assert "Aggressive: none" in report.text
    assert "All modes returned no safe candidate links." in report.text


def test_conservative_removed_vs_balanced_logic(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result(
        balanced=["L1", "L2", "L3"],
        conservative=["L1"],
    )

    report = builder.build(result)

    assert "Conservative removed compared to Balanced: L2, L3" in report.text


def test_aggressive_order_difference_logic(
    builder: PolicyShowcaseBuilder,
) -> None:
    result_diff = create_mock_comparison_result(
        balanced=["L1", "L2"],
        aggressive=["L2", "L1"],
    )
    report_diff = builder.build(result_diff)

    assert "Aggressive order differs from Balanced: yes" in report_diff.text

    result_same = create_mock_comparison_result(
        balanced=["L1", "L2"],
        aggressive=["L1", "L2"],
    )
    report_same = builder.build(result_same)

    assert "Aggressive order differs from Balanced: no" in report_same.text


def test_metadata_counts_match(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result(
        baseline=["L1", "L2", "L3"],
        conservative=["L1"],
        balanced=["L1", "L2"],
        aggressive=["L2", "L1", "L3", "L4"],
    )

    report = builder.build(result)

    assert report.metadata["baseline_count"] == 3
    assert report.metadata["conservative_count"] == 1
    assert report.metadata["balanced_count"] == 2
    assert report.metadata["aggressive_count"] == 4


def test_to_dict_mutation_safety(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result()
    report = builder.build(result)

    exported = report.to_dict()
    exported["metadata"]["builder_name"] = "HACKED"
    exported["title"] = "HACKED"

    exported_again = report.to_dict()

    assert exported_again["metadata"]["builder_name"] == "PolicyShowcaseBuilder"
    assert exported_again["title"] == "Phase-6 Runtime Policy Showcase"


def test_to_dict_schema_is_stable(
    builder: PolicyShowcaseBuilder,
) -> None:
    result = create_mock_comparison_result()
    exported = builder.build(result).to_dict()

    assert exported["type"] == "phase6_policy_showcase_report"
    assert exported["version"] == "1.0"
    assert exported["title"] == "Phase-6 Runtime Policy Showcase"
    assert exported["metadata"]["builder_name"] == "PolicyShowcaseBuilder"
    assert exported["metadata"]["builder_version"] == "1.0"