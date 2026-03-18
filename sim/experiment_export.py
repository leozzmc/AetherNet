import csv
import io
from pathlib import Path
from typing import Any, Dict, List

from sim.experiment_harness import ExperimentResult

# Deterministic and explicit column ordering for all CSV exports
EXPORT_COLUMNS = [
    "case_name",
    "scenario_name",
    "delivery_ratio",
    "unique_delivered",
    "duplicate_deliveries",
    "store_remaining",
    "bundles_dropped_total",
]


def experiment_result_to_row(result: ExperimentResult) -> Dict[str, Any]:
    """
    Wave-54: Flattens an ExperimentResult into a deterministic dictionary
    matching the EXPORT_COLUMNS order.
    """
    # Safely handle bundles_dropped_total if it happens to be a dict from legacy reports
    dropped = result.bundles_dropped_total
    if isinstance(dropped, dict):
        dropped_val = dropped.get("total", 0)
    else:
        dropped_val = dropped

    row = {
        "case_name": result.case_name,
        "scenario_name": result.scenario_name,
        "delivery_ratio": result.delivery_ratio,
        "unique_delivered": result.unique_delivered,
        "duplicate_deliveries": result.duplicate_deliveries,
        "store_remaining": len(result.store_bundle_ids_remaining),
        "bundles_dropped_total": dropped_val,
    }
    return row


def results_to_rows(results: List[ExperimentResult]) -> List[Dict[str, Any]]:
    """
    Converts a list of ExperimentResult objects into a list of flat rows,
    strictly preserving the input order.
    """
    return [experiment_result_to_row(r) for r in results]


def results_to_csv_string(results: List[ExperimentResult]) -> str:
    """
    Serializes a list of ExperimentResult objects into a deterministic CSV string.
    """
    if not results:
        # Return just the headers if there are no results
        return ",".join(EXPORT_COLUMNS) + "\r\n"

    rows = results_to_rows(results)
    output = io.StringIO()
    
    # Use explicit lineterminator for cross-platform deterministic output
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, lineterminator='\r\n')
    
    writer.writeheader()
    writer.writerows(rows)
    
    return output.getvalue()


def write_results_csv(results: List[ExperimentResult], output_path: str) -> str:
    """
    Writes a list of ExperimentResult objects to a CSV file deterministically.
    Returns the absolute path to the written file.
    """
    csv_content = results_to_csv_string(results)
    path = Path(output_path).resolve()
    
    # Ensure parent directories exist (if any)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
        
    path.write_text(csv_content, encoding="utf-8")
    return str(path)