from dataclasses import dataclass
from typing import Any, Dict, List

from .case_spec import BenchmarkCaseSpec


@dataclass(frozen=True)
class BenchmarkPack:
    """
    Deterministic suite of benchmark cases.
    """

    pack_name: str
    cases: List[BenchmarkCaseSpec]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.pack_name.strip():
            raise ValueError("pack_name must be a non-empty string")

        seen_case_ids = set()
        for case in self.cases:
            if case.case_id in seen_case_ids:
                raise ValueError(f"Duplicate case_id found in pack: {case.case_id}")
            seen_case_ids.add(case.case_id)

        object.__setattr__(self, "cases", list(self.cases))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @staticmethod
    def _sorted_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        return {key: data[key] for key in sorted(data.keys())}

    def to_dict(self) -> Dict[str, Any]:
        sorted_cases = sorted(self.cases, key=lambda case: case.case_id)

        return {
            "pack_name": self.pack_name,
            "metadata": self._sorted_metadata(self.metadata),
            "cases": [case.to_dict() for case in sorted_cases],
        }