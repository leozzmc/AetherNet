import csv
import io
from pathlib import Path

from sim.comparison_export import (
    COMPARISON_COLUMNS,
    comparison_row_to_table_row,
    comparison_to_rows,
    comparison_to_csv,
    write_comparison_csv,
)


def test_table_row_flattening_is_deterministic():
    raw_row = {
        "case_name": "test_case_A",
        "left_present": True,
        "right_present": True,
        "left_delivery_ratio": 0.4,
        "right_delivery_ratio": 0.6,
        "delivery_ratio_delta": 0.2,
        "left_raw": {"dummy": "data"},
        "right_raw": {"dummy": "data"}
    }
    
    flat_row = comparison_row_to_table_row(raw_row)
    
    assert flat_row["case_name"] == "test_case_A"
    assert flat_row["status"] == "both"
    assert flat_row["left_delivery_ratio"] == 0.4
    assert flat_row["right_delivery_ratio"] == 0.6
    assert flat_row["delivery_ratio_delta"] == 0.2
    
    # Ensure exactly the target columns are present
    assert set(flat_row.keys()) == set(COMPARISON_COLUMNS)


def test_status_field_is_correct_for_all_presence_combinations():
    row_both = {"left_present": True, "right_present": True}
    assert comparison_row_to_table_row(row_both)["status"] == "both"
    
    row_left = {"left_present": True, "right_present": False}
    assert comparison_row_to_table_row(row_left)["status"] == "only_left"
    
    row_right = {"left_present": False, "right_present": True}
    assert comparison_row_to_table_row(row_right)["status"] == "only_right"


def test_comparison_to_rows_preserves_deterministic_ordering():
    comparison_data = {
        "rows": [
            {"case_name": "case-1", "left_present": True, "right_present": True},
            {"case_name": "case-2", "left_present": True, "right_present": False},
            {"case_name": "case-3", "left_present": False, "right_present": True},
        ]
    }
    
    rows = comparison_to_rows(comparison_data)
    
    assert len(rows) == 3
    assert rows[0]["case_name"] == "case-1"
    assert rows[1]["case_name"] == "case-2"
    assert rows[2]["case_name"] == "case-3"


def test_csv_output_column_order_is_stable():
    comparison_data = {
        "rows": [
            {
                "case_name": "test-case",
                "left_present": True,
                "right_present": True,
                "left_delivery_ratio": 0.5,
                "right_delivery_ratio": 0.5,
                "delivery_ratio_delta": 0.0
            }
        ]
    }
    
    csv_str = comparison_to_csv(comparison_data)
    
    reader = csv.reader(io.StringIO(csv_str))
    header = next(reader)
    
    assert header == COMPARISON_COLUMNS
    
    data_row = next(reader)
    assert data_row[0] == "test-case"
    assert data_row[1] == "both"
    assert data_row[2] == "0.5"


def test_empty_comparison_yields_headers_only():
    comparison_data = {"rows": []}
    csv_str = comparison_to_csv(comparison_data)
    assert csv_str.strip() == ",".join(COMPARISON_COLUMNS)


def test_file_writer_writes_deterministic_output(tmp_path):
    comparison_data = {
        "rows": [
            {
                "case_name": "test-file-case",
                "left_present": True,
                "right_present": True,
                "left_delivery_ratio": 0.1,
                "right_delivery_ratio": 0.9,
                "delivery_ratio_delta": 0.8
            }
        ]
    }
    
    out_file = tmp_path / "comparison.csv"
    written_path = write_comparison_csv(comparison_data, str(out_file))
    
    assert Path(written_path).exists()
    
    content = Path(written_path).read_text(encoding="utf-8")
    assert "case_name,status" in content
    assert "test-file-case,both,0.1,0.9,0.8" in content