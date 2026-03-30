from dataclasses import dataclass
from typing import Any, Dict, List

from .case_result import BenchmarkCaseResult


@dataclass(frozen=True)
class BenchmarkPackResult:
    """
    Aggregate deterministic result for a full benchmark pack execution.
    """

    pack_name: str
    case_results: List[BenchmarkCaseResult]
    summary: Dict[str, int]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_results", list(self.case_results))
        object.__setattr__(self, "summary", dict(self.summary))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @staticmethod
    def _sorted_dict(data: Dict[str, int]) -> Dict[str, int]:
        return {key: data[key] for key in sorted(data.keys())}

    def to_dict(self) -> Dict[str, Any]:
        sorted_results = sorted(self.case_results, key=lambda result: result.case_id)

        exported_metadata = {
            "runner_name": self.metadata.get("runner_name"),
            "runner_version": self.metadata.get("runner_version"),
        }

        return {
            "type": "benchmark_pack_result",
            "version": "1.0",
            "pack_name": self.pack_name,
            "summary": self._sorted_dict(self.summary),
            "metadata": exported_metadata,
            "case_results": [result.to_dict() for result in sorted_results],
        }