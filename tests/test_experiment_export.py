import csv
import io
from pathlib import Path

from sim.experiment_harness import ExperimentCase, ExperimentHarness, ExperimentResult
from sim.experiment_export import (
    EXPORT_COLUMNS,
    experiment_result_to_row,
    results_to_rows,
    results_to_csv_string,
    write_results_csv,
)


def make_dummy_result(case_name: str, delivery_ratio: float) -> ExperimentResult:
    return ExperimentResult(
        case_name=case_name,
        scenario_name="test_scenario",
        final_metrics={},
        delivered_bundle_ids=["b1", "b2"],
        store_bundle_ids_remaining=["b3"],
        delivery_ratio=delivery_ratio,
        unique_delivered=2,
        duplicate_deliveries=1,
        bundles_dropped_total=0,
    )


def test_row_flattening_is_deterministic():
    result = make_dummy_result("case-A", 0.5)
    row = experiment_result_to_row(result)

    assert row["case_name"] == "case-A"
    assert row["scenario_name"] == "test_scenario"
    assert row["delivery_ratio"] == 0.5
    assert row["unique_delivered"] == 2
    assert row["duplicate_deliveries"] == 1
    # Store remaining is evaluated via length of store_bundle_ids_remaining
    assert row["store_remaining"] == 1 
    assert row["bundles_dropped_total"] == 0

    # Ensure the row exactly matches the expected explicit column schema
    assert set(row.keys()) == set(EXPORT_COLUMNS)


def test_results_to_rows_preserves_ordering():
    r1 = make_dummy_result("case-1", 0.1)
    r2 = make_dummy_result("case-2", 0.2)
    r3 = make_dummy_result("case-3", 0.3)

    rows = results_to_rows([r1, r2, r3])

    assert len(rows) == 3
    assert rows[0]["case_name"] == "case-1"
    assert rows[1]["case_name"] == "case-2"
    assert rows[2]["case_name"] == "case-3"


def test_csv_output_column_order_is_stable():
    r1 = make_dummy_result("case-1", 0.1)
    csv_str = results_to_csv_string([r1])

    # Parse back the generated CSV string to verify its structural integrity
    reader = csv.reader(io.StringIO(csv_str))
    header = next(reader)

    assert header == EXPORT_COLUMNS

    data_row = next(reader)
    assert data_row[0] == "case-1"
    assert data_row[1] == "test_scenario"
    assert data_row[2] == "0.1"


def test_empty_results_yield_headers_only():
    csv_str = results_to_csv_string([])
    assert csv_str.strip() == ",".join(EXPORT_COLUMNS)


def test_file_writer_writes_deterministic_output(tmp_path):
    r1 = make_dummy_result("case-1", 0.1)
    r2 = make_dummy_result("case-2", 0.9)

    out_file = tmp_path / "results.csv"
    written_path = write_results_csv([r1, r2], str(out_file))

    assert Path(written_path).exists()

    content = Path(written_path).read_text(encoding="utf-8")
    assert "case_name,scenario_name" in content
    assert "case-1,test_scenario,0.1" in content
    assert "case-2,test_scenario,0.9" in content


def test_export_layer_works_with_real_experiment_harness_results():
    cases = [
        ExperimentCase(
            case_name="integration-case", 
            scenario_name="default_multihop", 
            tick_size=1, 
            simulation_end_override=10
        )
    ]
    
    # Generate real results from the simulator harness
    results = ExperimentHarness.run_experiments(cases)
    assert len(results) == 1

    # Ensure they serialize properly
    csv_str = results_to_csv_string(results)
    
    assert "integration-case" in csv_str
    assert "default_multihop" in csv_str