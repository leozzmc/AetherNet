import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_batch_summary(bundle_dir: str) -> List[Dict[str, Any]]:
    """
    Wave-57: Reads summary.csv from a given artifact bundle directory.
    Returns a list of row dictionaries (no indexing).
    """
    bundle_path = Path(bundle_dir).resolve()
    csv_path = bundle_path / "summary.csv"

    if not csv_path.is_file():
        raise ValueError(f"Missing summary.csv in bundle directory: {bundle_path}")

    rows: List[Dict[str, Any]] = []

    content = csv_path.read_text(encoding="utf-8")
    reader = csv.DictReader(content.splitlines())

    for row in reader:
        case_name = row.get("case_name")
        if not case_name:
            continue

        parsed_row = dict(row)

        # Safe numeric parsing
        raw_ratio = row.get("delivery_ratio")
        try:
            parsed_row["delivery_ratio"] = float(raw_ratio) if raw_ratio is not None else None
        except (ValueError, TypeError):
            parsed_row["delivery_ratio"] = None

        rows.append(parsed_row)

    return rows


def _index_by_case_name(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Internal helper: builds index for comparison layer only.
    """
    index = {}
    for r in rows:
        case_name = r.get("case_name")
        if case_name:
            index[case_name] = r
    return index


def compare_batch_dirs(left_bundle_dir: str, right_bundle_dir: str) -> Dict[str, Any]:
    """
    Wave-57: Performs deterministic FULL OUTER JOIN on case_name.
    """

    left_rows = read_batch_summary(left_bundle_dir)
    right_rows = read_batch_summary(right_bundle_dir)

    left_cases = _index_by_case_name(left_rows)
    right_cases = _index_by_case_name(right_rows)

    all_case_names = set(left_cases.keys()).union(set(right_cases.keys()))
    sorted_case_names = sorted(all_case_names)

    comparison_rows = []

    for case_name in sorted_case_names:
        left_row = left_cases.get(case_name)
        right_row = right_cases.get(case_name)

        left_present = left_row is not None
        right_present = right_row is not None

        left_ratio = left_row.get("delivery_ratio") if left_present else None
        right_ratio = right_row.get("delivery_ratio") if right_present else None

        delta: Optional[float] = None
        if left_ratio is not None and right_ratio is not None:
            delta = right_ratio - left_ratio  # no rounding

        comparison_rows.append({
            "case_name": case_name,
            "left_present": left_present,
            "right_present": right_present,
            "left_delivery_ratio": left_ratio,
            "right_delivery_ratio": right_ratio,
            "delivery_ratio_delta": delta,
            "left_raw": left_row,
            "right_raw": right_row,
        })

    return {
        "left_batch_dir": str(Path(left_bundle_dir).resolve()),
        "right_batch_dir": str(Path(right_bundle_dir).resolve()),
        "total_cases_compared": len(comparison_rows),
        "rows": comparison_rows,
    }


def compare_batches_from_catalog(
    catalog: Dict[str, Any],
    left_label: str,
    right_label: str
) -> Dict[str, Any]:
    """
    Wave-57: Catalog-aware comparison.
    """

    batches = catalog.get("batches", [])

    left_path = None
    right_path = None

    for batch in batches:
        if batch.get("batch_label") == left_label:
            left_path = batch.get("path")
        if batch.get("batch_label") == right_label:
            right_path = batch.get("path")

    if not left_path:
        raise ValueError(f"Batch label '{left_label}' not found in catalog.")
    if not right_path:
        raise ValueError(f"Batch label '{right_label}' not found in catalog.")

    return compare_batch_dirs(left_path, right_path)


def comparison_to_json(comparison: Dict[str, Any]) -> str:
    """
    Deterministic JSON serialization.
    """
    return json.dumps(comparison, indent=2, sort_keys=True)
  