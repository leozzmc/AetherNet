from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RouteCandidate:
    """
    Wave-40: Represents a potential next hop with a deterministic score.
    Higher scores represent better routes (e.g., lower latency, higher bandwidth proxy).
    """
    next_hop: str
    score: int = 0


class RouteScorer:
    """
    Deterministic scoring engine for selecting the best next hop among multiple candidates.
    """
    @staticmethod
    def choose_best(candidates: List[RouteCandidate]) -> Optional[str]:
        if not candidates:
            return None

        # Sort candidates deterministically:
        # 1. By score descending (highest score first)
        # 2. By next_hop ascending (lexical order tie-breaker)
        sorted_candidates = sorted(
            candidates, 
            key=lambda c: (-c.score, c.next_hop)
        )
        
        return sorted_candidates[0].next_hop