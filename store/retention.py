from typing import List
from store.store import DTNStore

def expired_bundle_ids(store: DTNStore, current_time: int) -> List[str]:
    """Finds all bundles in the store that have exceeded their TTL."""
    expired = []
    for bundle_id in store.list_bundle_ids():
        try:
            bundle = store.load_bundle(bundle_id)
            if bundle.is_expired(current_time):
                expired.append(bundle_id)
        except (FileNotFoundError, ValueError):
            continue
    return expired

def purge_expired(store: DTNStore, current_time: int) -> List[str]:
    """Deletes all expired bundles from the store and returns their IDs."""
    purged = []
    for bundle_id in expired_bundle_ids(store, current_time):
        store.delete_bundle(bundle_id)
        purged.append(bundle_id)
    return purged