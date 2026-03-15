from typing import List, Dict, Any

from store.store import DTNStore
from bundle_queue.priority_queue import StrictPriorityQueue
from router.contact_manager import Contact
from link.capacity_manager import ContactWindowCapacityManager


def compute_store_depth_final(store: DTNStore) -> int:
    """Calculate the final number of bundles resting in the persistent DTN store."""
    return len(store.list_bundle_ids())


def compute_queue_depth_final(lunar_queue: StrictPriorityQueue, relay_queue: StrictPriorityQueue) -> Dict[str, int]:
    """Summarize the final number of bundles stuck in memory queues awaiting transit."""
    return {
        "lunar": lunar_queue.size(),
        "relay": relay_queue.size()
    }


def compute_link_utilization(
    contacts: List[Contact], 
    capacity_manager: ContactWindowCapacityManager
) -> List[Dict[str, Any]]:
    """
    Generate a utilization report for all explicitly capacity-limited contact windows.
    
    Rules:
    - Unlimited contacts (capacity_bundles is None) are completely omitted.
    - Zero-capacity contacts output None for utilization_ratio to prevent division by zero.
    - Finite-capacity contacts output a float utilization_ratio (used / capacity).
    """
    utilization_report = []

    for contact in contacts:
        if contact.capacity_bundles is None:
            continue  # Omit unlimited links from utilization reports

        used = capacity_manager.get_usage(contact)
        remaining = capacity_manager.remaining_bundle_capacity(contact)
        
        ratio = None
        if contact.capacity_bundles > 0:
            ratio = float(used) / float(contact.capacity_bundles)

        utilization_report.append({
            "source": contact.source,
            "target": contact.target,
            "start_time": contact.start_time,
            "end_time": contact.end_time,
            "capacity_bundles": contact.capacity_bundles,
            "used_bundles": used,
            "remaining_bundles": remaining,
            "utilization_ratio": ratio
        })

    # Sort deterministically by start_time, then source, then target
    utilization_report.sort(key=lambda x: (x["start_time"], x["source"], x["target"]))
    return utilization_report