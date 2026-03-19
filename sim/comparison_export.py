import csv
import io
from pathlib import Path
from typing import Any, Dict, List

# Deterministic and explicit column ordering for paper-ready comparison CSVs
COMPARISON_COLUMNS = [
    "case_name",
    "status",
    "left_delivery_ratio",
    "right_delivery_ratio",
    "delivery_ratio_delta"
]


def comparison_row_to_table_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wave-58: Flattens a Wave-57 comparison row into a paper-ready flat dictionary.
    Derives a human-readable 'status' field based on presence flags.
    """
    left_present = row.get("left_present", False)
    right_present = row.get("right_present", False)

    if left_present and right_present:
        status = "both"
    elif left_present and not right_present:
        status = "only_left"
    elif not left_present and right_present:
        status = "only_right"
    else:
        # Should mathematically not happen based on Wave-57 FULL OUTER JOIN,
        # but safe fallback for structural completeness.
        status = "neither"

    return {
        "case_name": row.get("case_name", "unknown"),
        "status": status,
        "left_delivery_ratio": row.get("left_delivery_ratio"),
        "right_delivery_ratio": row.get("right_delivery_ratio"),
        "delivery_ratio_delta": row.get("delivery_ratio_delta")
    }


def comparison_to_rows(comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Converts a full Wave-57 comparison dictionary into a list of flat table rows.
    Preserves the exact ordering provided by the comparison engine.
    """
    raw_rows = comparison.get("rows", [])
    return [comparison_row_to_table_row(r) for r in raw_rows]


def comparison_to_csv(comparison: Dict[str, Any]) -> str:
    """
    Serializes a Wave-57 comparison dictionary into a deterministic CSV string.
    """
    rows = comparison_to_rows(comparison)
    
    if not rows:
        return ",".join(COMPARISON_COLUMNS) + "\r\n"

    output = io.StringIO()
    # Explicit lineterminator for cross-platform stability
    writer = csv.DictWriter(output, fieldnames=COMPARISON_COLUMNS, lineterminator='\r\n')
    
    writer.writeheader()
    writer.writerows(rows)
    
    return output.getvalue()


def write_comparison_csv(comparison: Dict[str, Any], output_path: str) -> str:
    """
    Writes a comparison result to a CSV file deterministically.
    Returns the absolute path to the written file.
    """
    csv_content = comparison_to_csv(comparison)
    path = Path(output_path).resolve()
    
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
        
    path.write_text(csv_content, encoding="utf-8")
    return str(path)