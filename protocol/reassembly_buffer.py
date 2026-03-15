from typing import Dict, List
from router.bundle import Bundle

class ReassemblyBuffer:
    """
    A simple, deterministic buffer to hold incoming bundle fragments 
    until a complete set is ready for reassembly.
    """
    def __init__(self) -> None:
        # Maps original_bundle_id -> List of fragment Bundles
        self._fragments: Dict[str, List[Bundle]] = {}

    def add(self, fragment: Bundle) -> None:
        if not fragment.is_fragment or not fragment.original_bundle_id:
            return
            
        bundle_id = fragment.original_bundle_id
        if bundle_id not in self._fragments:
            self._fragments[bundle_id] = []
            
        self._fragments[bundle_id].append(fragment)

    def get(self, bundle_id: str) -> List[Bundle]:
        return self._fragments.get(bundle_id, [])

    def remove(self, bundle_id: str) -> None:
        self._fragments.pop(bundle_id, None)