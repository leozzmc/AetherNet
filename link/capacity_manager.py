from typing import Dict, Optional, Tuple

from router.contact_manager import Contact


class ContactWindowCapacityManager:
    """
    Tracks bundle-count usage for individual contact windows.

    A contact window is uniquely identified by:
        (source, target, start_time, end_time)

    Capacity semantics:
    - capacity_bundles=None -> unlimited
    - capacity_bundles=0    -> blocked
    - capacity_bundles=n    -> finite bundle-count limit
    """

    def __init__(self) -> None:
        self._usage: Dict[Tuple[str, str, int, int], int] = {}

    def _get_key(self, contact: Contact) -> Tuple[str, str, int, int]:
        return (contact.source, contact.target, contact.start_time, contact.end_time)

    def can_forward(self, contact: Contact) -> bool:
        if contact.capacity_bundles is None:
            return True

        if contact.capacity_bundles == 0:
            return False

        key = self._get_key(contact)
        current_usage = self._usage.get(key, 0)
        return current_usage < contact.capacity_bundles

    def record_forward(self, contact: Contact) -> None:
        """
        Record one successful forwarding event for this contact window.

        Raises:
            ValueError: if the contact window has no remaining capacity.
        """
        if contact.capacity_bundles is None:
            return

        if not self.can_forward(contact):
            raise ValueError(
                f"Cannot record forward for exhausted contact window: "
                f"{contact.source}->{contact.target} "
                f"[{contact.start_time}, {contact.end_time})"
            )

        key = self._get_key(contact)
        self._usage[key] = self._usage.get(key, 0) + 1

    def remaining_bundle_capacity(self, contact: Contact) -> Optional[int]:
        if contact.capacity_bundles is None:
            return None

        key = self._get_key(contact)
        current_usage = self._usage.get(key, 0)
        return max(0, contact.capacity_bundles - current_usage)

    def reset(self) -> None:
        self._usage.clear()