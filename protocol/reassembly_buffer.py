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

    def collect_garbage(self, current_time: int) -> List[str]:
        """
        Wave-31: Deterministic fragment garbage collection.

        Remove any fragment set from the reassembly buffer if any fragment
        in that set is expired at the given current_time.

        Returns:
            A sorted list of removed original_bundle_id values.
        """
        if current_time < 0:
            raise ValueError("current_time must be >= 0 for garbage collection.")

        removed_bundle_ids: List[str] = []

        for bundle_id, fragments in list(self._fragments.items()):
            if any(fragment.is_expired(current_time) for fragment in fragments):
                removed_bundle_ids.append(bundle_id)

        for bundle_id in removed_bundle_ids:
            self.remove(bundle_id)

        removed_bundle_ids.sort()
        return removed_bundle_ids