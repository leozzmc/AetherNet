from dataclasses import dataclass
from typing import Any, Dict, List

from .comparison import PolicyComparisonResult


@dataclass(frozen=True)
class PolicyShowcaseReport:
    """
    Deterministic presentation artifact for Phase-6 policy comparison results.
    """

    case_id: str
    title: str
    text: str
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")

        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        exported_metadata = {
            "builder_name": self.metadata.get("builder_name", "PolicyShowcaseBuilder"),
            "builder_version": self.metadata.get("builder_version", "1.0"),
            "line_count": self.metadata.get("line_count", 0),
            "baseline_count": self.metadata.get("baseline_count", 0),
            "conservative_count": self.metadata.get("conservative_count", 0),
            "balanced_count": self.metadata.get("balanced_count", 0),
            "aggressive_count": self.metadata.get("aggressive_count", 0),
        }

        return {
            "type": "phase6_policy_showcase_report",
            "version": "1.0",
            "case_id": self.case_id,
            "title": self.title,
            "text": self.text,
            "metadata": exported_metadata,
        }


class PolicyShowcaseBuilder:
    """
    Deterministic renderer that converts PolicyComparisonResult into
    a stable plain-text showcase report.
    """

    @staticmethod
    def _format_list(items: List[str]) -> str:
        return ", ".join(list(items)) if items else "none"

    @staticmethod
    def _ordered_difference(
        left: List[str],
        right: List[str],
    ) -> List[str]:
        right_set = set(right)
        return [item for item in left if item not in right_set]

    def build(self, result: PolicyComparisonResult) -> PolicyShowcaseReport:
        removed_vs_balanced = self._ordered_difference(
            result.balanced_candidates,
            result.conservative_candidates,
        )
        order_differs = (
            "yes"
            if result.aggressive_candidates != result.balanced_candidates
            else "no"
        )

        all_modes_empty = (
            not result.baseline_candidates
            and not result.conservative_candidates
            and not result.balanced_candidates
            and not result.aggressive_candidates
        )

        lines: List[str] = [
            "=== Phase-6 Runtime Policy Showcase ===",
            f"Case: {result.case_id}",
            "",
            "[Candidate Outputs]",
            f"Baseline: {self._format_list(result.baseline_candidates)}",
            f"Conservative: {self._format_list(result.conservative_candidates)}",
            f"Balanced: {self._format_list(result.balanced_candidates)}",
            f"Aggressive: {self._format_list(result.aggressive_candidates)}",
            "",
            "[Policy Differences]",
            (
                "Conservative removed compared to Balanced: "
                f"{self._format_list(removed_vs_balanced)}"
            ),
            f"Aggressive order differs from Balanced: {order_differs}",
            "",
            "[Interpretation]",
        ]

        if all_modes_empty:
            lines.append(
                "All modes returned no safe candidate links. "
                "The network state is highly hostile."
            )
        else:
            lines.append(
                "Conservative mode reduces routing freedom when safer preferred links exist."
            )
            lines.append(
                "Aggressive mode preserves original safe ordering while still excluding avoid links."
            )

        report_text = "\n".join(lines)

        metadata: Dict[str, Any] = {
            "builder_name": "PolicyShowcaseBuilder",
            "builder_version": "1.0",
            "line_count": len(lines),
            "baseline_count": len(result.baseline_candidates),
            "conservative_count": len(result.conservative_candidates),
            "balanced_count": len(result.balanced_candidates),
            "aggressive_count": len(result.aggressive_candidates),
        }

        return PolicyShowcaseReport(
            case_id=result.case_id,
            title="Phase-6 Runtime Policy Showcase",
            text=report_text,
            metadata=metadata,
        )