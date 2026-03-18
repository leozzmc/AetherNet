from sim.experiment_harness import ExperimentCase, ExperimentHarness


def test_experiment_case_ordering_is_preserved():
    cases = [
        ExperimentCase(case_name="case-1", scenario_name="default_multihop"),
        ExperimentCase(case_name="case-2", scenario_name="delayed_delivery"),
        ExperimentCase(case_name="case-3", scenario_name="expiry_before_contact"),
    ]

    results = ExperimentHarness.run_experiments(cases)

    assert [result.case_name for result in results] == [
        "case-1",
        "case-2",
        "case-3",
    ]


def test_multiple_cases_run_deterministically():
    cases = [
        ExperimentCase(case_name="baseline-a", scenario_name="default_multihop"),
        ExperimentCase(case_name="baseline-b", scenario_name="delayed_delivery"),
    ]

    run_1 = ExperimentHarness.run_experiments(cases)
    run_2 = ExperimentHarness.run_experiments(cases)

    assert [result.case_name for result in run_1] == [result.case_name for result in run_2]
    assert [result.delivery_ratio for result in run_1] == [result.delivery_ratio for result in run_2]
    assert [result.unique_delivered for result in run_1] == [result.unique_delivered for result in run_2]
    assert [result.duplicate_deliveries for result in run_1] == [result.duplicate_deliveries for result in run_2]
    assert [result.delivered_bundle_ids for result in run_1] == [result.delivered_bundle_ids for result in run_2]


def test_results_include_harness_delivery_fields():
    cases = [
        ExperimentCase(case_name="delivery-check", scenario_name="default_multihop"),
    ]

    results = ExperimentHarness.run_experiments(cases)

    assert len(results) == 1
    result = results[0]

    assert hasattr(result, "delivery_ratio")
    assert hasattr(result, "unique_delivered")
    assert hasattr(result, "duplicate_deliveries")

    assert isinstance(result.delivery_ratio, float)
    assert isinstance(result.unique_delivered, int)
    assert isinstance(result.duplicate_deliveries, int)

    assert isinstance(result.final_metrics, dict)
    assert isinstance(result.delivered_bundle_ids, list)
    assert isinstance(result.store_bundle_ids_remaining, list)


def test_summary_helper_produces_stable_comparison_output():
    cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
    ]

    results = ExperimentHarness.run_experiments(cases)
    summary = ExperimentHarness.generate_summary(results)

    assert summary["total_cases"] == 2
    assert [case["case_name"] for case in summary["cases"]] == ["case-a", "case-b"]

    first_case = summary["cases"][0]
    assert "scenario_name" in first_case
    assert "delivery_ratio" in first_case
    assert "unique_delivered" in first_case
    assert "duplicate_deliveries" in first_case
    assert "bundles_dropped_total" in first_case
    assert "store_remaining" in first_case


def test_invalid_scenario_name_raises_value_error():
    cases = [
        ExperimentCase(case_name="bad-case", scenario_name="not_a_real_scenario"),
    ]

    try:
        ExperimentHarness.run_experiments(cases)
        assert False, "Expected ValueError for invalid scenario name"
    except ValueError as exc:
        message = str(exc)
        assert "bad-case" in message
        assert "failed" in message