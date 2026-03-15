from typing import List, Dict, Any

from store.store import DTNStore
from bundle_queue.priority_queue import StrictPriorityQueue
from router.contact_manager import Contact
from link.capacity_manager import ContactWindowCapacityManager


def compute_store_depth_final(store: DTNStore) -> int:
    """Calculate the final number of bundles resting in the persistent DTN store."""
    return len(store.list_bundle_ids())


def compute_queue_depth_final(*args) -> Dict[str, int]:
    """
    Backward-compatible queue depth summary.

    Supported forms:
    1. compute_queue_depth_final(node_queues_dict)
       where node_queues_dict is {node_name: queue}
    2. compute_queue_depth_final(lunar_queue, relay_queue)
       legacy Wave-18 / older test style
    """
    if len(args) == 1 and isinstance(args[0], dict):
        node_queues: Dict[str, StrictPriorityQueue] = args[0]
        return {
            node_name.replace("-", "_"): q.size()
            for node_name, q in node_queues.items()
        }

    if len(args) == 2:
        lunar_queue, relay_queue = args
        return {
            "lunar": lunar_queue.size(),
            "relay": relay_queue.size(),
        }

    raise TypeError(
        "compute_queue_depth_final expects either "
        "(node_queues_dict) or (lunar_queue, relay_queue)"
    )


def compute_link_utilization(
    contacts: List[Contact],
    capacity_manager: ContactWindowCapacityManager,
) -> List[Dict[str, Any]]:
    utilization_report = []

    for contact in contacts:
        if contact.capacity_bundles is None:
            continue

        used = capacity_manager.get_usage(contact)
        remaining = capacity_manager.remaining_bundle_capacity(contact)

        ratio = None
        if contact.capacity_bundles > 0:
            ratio = float(used) / float(contact.capacity_bundles)

        utilization_report.append(
            {
                "source": contact.source,
                "target": contact.target,
                "start_time": contact.start_time,
                "end_time": contact.end_time,
                "capacity_bundles": contact.capacity_bundles,
                "used_bundles": used,
                "remaining_bundles": remaining,
                "utilization_ratio": ratio,
            }
        )

    utilization_report.sort(key=lambda x: (x["start_time"], x["source"], x["target"]))
    return utilization_report