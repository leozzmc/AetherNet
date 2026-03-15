import argparse
import json
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from collections import defaultdict

from router.bundle import Bundle, BundleStatus
from router.contact_manager import ContactManager, Contact
from router.app import AetherRouter
from router.forwarding import ForwardingEngine
from bundle_queue.priority_queue import StrictPriorityQueue
from bundle_queue.classifiers import classify_bundle
from store.store import DTNStore
from store.retention import expired_bundle_ids, purge_expired
from sim.event_loop import SimulationClock
from metrics.exporter import MetricsCollector
from sim.scenarios import get_scenario
from sim.reporting import write_json_report
from link.capacity_manager import ContactWindowCapacityManager
from metrics.network_metrics import (
    compute_store_depth_final,
    compute_queue_depth_final,
    compute_link_utilization
)


RETENTION_INTERVAL = 5


class Simulator:
    """Configurable multi-hop application-layer simulator.

    Backward-compatibility:
    - New style:
        Simulator(router, store, lunar_queue, relay_queue, clock, metrics, ...)
    - Old style:
        Simulator(contact_manager, store, queue, clock)
    """

    def __init__(
        self,
        router_or_contact_manager,
        store: DTNStore,
        lunar_queue: StrictPriorityQueue,
        relay_queue_or_clock=None,
        clock: Optional[SimulationClock] = None,
        metrics: Optional[MetricsCollector] = None,
        scenario_name: str = "custom",
        injected_bundle_ids: Optional[List[str]] = None,
    ) -> None:
        if isinstance(router_or_contact_manager, ContactManager):
            self.contact_manager = router_or_contact_manager
            self.router = AetherRouter(self.contact_manager)

            if isinstance(relay_queue_or_clock, SimulationClock) and clock is None:
                clock = relay_queue_or_clock
                relay_queue = StrictPriorityQueue()
            else:
                relay_queue = relay_queue_or_clock if relay_queue_or_clock is not None else StrictPriorityQueue()
        else:
            self.router = router_or_contact_manager

            # Resolve contact manager from the router in a backward-compatible way.
            self.contact_manager = (
                getattr(self.router, "contact_manager", None)
                or getattr(self.router, "cm", None)
                or getattr(self.router, "_contact_manager", None)
            )
            if self.contact_manager is None:
                raise TypeError(
                    "Simulator requires either a ContactManager or a router exposing "
                    "contact_manager/cm/_contact_manager"
                )

            relay_queue = relay_queue_or_clock if relay_queue_or_clock is not None else StrictPriorityQueue()

        if clock is None:
            raise TypeError("clock is required")

        self.store = store
        self.lunar_queue = lunar_queue
        self.relay_queue = relay_queue
        self.clock = clock
        self.metrics = metrics if metrics is not None else MetricsCollector()
        self.scenario_name = scenario_name
        self.lunar_link_up = False
        self.relay_link_up = False
        self.delivered_bundle_ids: List[str] = []
        self.injected_bundle_ids: List[str] = sorted(injected_bundle_ids or [])
        self.bundle_timelines: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.capacity_manager = ContactWindowCapacityManager()

    def _record_timeline_event(self, bundle_id: str, event_key: str, current_time: int) -> None:
        """Record the first occurrence of a specific lifecycle event for a bundle."""
        if event_key not in self.bundle_timelines[bundle_id]:
            self.bundle_timelines[bundle_id][event_key] = current_time

    def _update_link_logs(self, current_time: int) -> None:
        lunar_up = self.router.can_forward_destination("lunar-node", "ground-station", current_time)
        relay_up = self.router.can_forward_destination("leo-relay", "ground-station", current_time)

        if lunar_up and not self.lunar_link_up:
            print(f"[t={current_time:02d}] link up: lunar-node -> leo-relay")
        elif not lunar_up and self.lunar_link_up:
            print(f"[t={current_time:02d}] link down: lunar-node -> leo-relay")

        if relay_up and not self.relay_link_up:
            print(f"[t={current_time:02d}] link up: leo-relay -> ground-station")
        elif not relay_up and self.relay_link_up:
            print(f"[t={current_time:02d}] link down: leo-relay -> ground-station")

        self.lunar_link_up = lunar_up
        self.relay_link_up = relay_up

    def _apply_retention(self, current_time: int) -> None:
        if current_time <= 0 or current_time % RETENTION_INTERVAL != 0:
            return

        expired_ids = expired_bundle_ids(self.store, current_time)
        if not expired_ids:
            return

        expired_types: Dict[str, str] = {}
        for bundle_id in expired_ids:
            try:
                expired_types[bundle_id] = self.store.load_bundle(bundle_id).type
            except (FileNotFoundError, ValueError):
                expired_types[bundle_id] = "unknown"

        purged_ids = purge_expired(self.store, current_time)
        for bundle_id in purged_ids:
            print(f"[t={current_time:02d}] purged expired bundle {bundle_id} from store")
            self.metrics.record_expired(expired_types.get(bundle_id, "unknown"), bundle_id)
            self._record_timeline_event(bundle_id, "purged_tick", current_time)

    def _find_matching_contact(
        self,
        current_node: str,
        next_hop: Optional[str],
        current_time: int,
    ) -> Optional[Contact]:
        """
        Find an active contact that can carry traffic from current_node.

        Preferred behavior:
        - if next_hop is known, find the matching active contact for that hop
        - if next_hop is None, fall back to the first active outgoing contact
          from current_node (backward compatibility for older tests/scenarios)
        """
        active_contacts = self.contact_manager.get_active_contacts(current_time)

        if next_hop is not None:
            for contact in active_contacts:
                if contact.allows(current_node, next_hop):
                    return contact
            return None

        # Backward-compatible fallback:
        # choose the first active contact that can carry traffic out of current_node
        for contact in active_contacts:
            if contact.source == current_node:
                return contact
            if contact.bidirectional and contact.target == current_node:
                return contact

        return None

    def _process_hop(self, current_node: str, outbound_queue: StrictPriorityQueue, current_time: int) -> Optional[Bundle]:
        if outbound_queue.size() == 0:
            return None

        bundle = outbound_queue.peek(current_time)
        if bundle is None:
            return None

        next_hop = self.router.get_next_hop(current_node, bundle.destination)
        contact = self._find_matching_contact(current_node, next_hop, current_time)
        if contact is None:
            return None

        # If policy could not resolve next hop, derive it from the matched contact
        # for backward compatibility with older tests/scenarios.
        if next_hop is None:
            if contact.source == current_node:
                next_hop = contact.target
            else:
                next_hop = contact.source

        if not self.capacity_manager.can_forward(contact):
            return None

        bundle = outbound_queue.dequeue(current_time)
        if bundle is None:
            return None

        # Defensive consistency check: the dequeued bundle should still map to the same next hop.
        resolved_next_hop = self.router.get_next_hop(current_node, bundle.destination)
        if resolved_next_hop is not None and resolved_next_hop != next_hop:
            raise RuntimeError(
                f"Queue head changed unexpectedly during forwarding decision at {current_node} "
                f"for bundle {bundle.id}"
            )

        self.capacity_manager.record_forward(contact)

        ForwardingEngine.begin_forward(bundle)
        self.store.save_bundle(bundle)
        self.metrics.record_forwarded(bundle.type)
        self._record_timeline_event(bundle.id, "first_forwarded_tick", current_time)

        print(f"[t={current_time:02d}] forwarding {bundle.type} {bundle.id} to {next_hop}")

        ForwardingEngine.complete_forward(bundle, current_node)
        self.store.save_bundle(bundle)

        if bundle.status == BundleStatus.DELIVERED:
            self.metrics.record_delivered(bundle.type)
            self.delivered_bundle_ids.append(bundle.id)
            self._record_timeline_event(bundle.id, "delivered_tick", current_time)
            print(f"[t={current_time:02d}] {bundle.id} delivered to {bundle.destination}")
        else:
            self.metrics.record_stored(bundle.type)
            self._record_timeline_event(bundle.id, "stored_tick", current_time)
            print(f"[t={current_time:02d}] {bundle.id} stored at {next_hop}")

        return bundle

    def tick(self, current_time: int) -> None:
        self._update_link_logs(current_time)
        self._apply_retention(current_time)

        moved_to_relay = self._process_hop("lunar-node", self.lunar_queue, current_time)
        if moved_to_relay is not None and moved_to_relay.status == BundleStatus.STORED:
            self.relay_queue.enqueue(moved_to_relay)

        self._process_hop("leo-relay", self.relay_queue, current_time)

        self.metrics.set_queue_depth("queue_depth_lunar", self.lunar_queue.size())
        self.metrics.set_queue_depth("queue_depth_relay", self.relay_queue.size())

    def run(self) -> Dict[str, Any]:
        for t in self.clock.ticks():
            self.tick(t)
        return self.build_final_report()

    def build_final_report(self) -> Dict[str, Any]:
        store_remaining = sorted(self.store.list_bundle_ids())
        metrics_snap = self.metrics.snapshot()

        report = {
            "scenario_name": self.scenario_name,
            "simulation_start_time": self.clock.start_time,
            "simulation_end_time": self.clock.end_time,
            "tick_size": self.clock.tick_size,
            "final_metrics": metrics_snap,
            "store_bundle_ids_remaining": store_remaining,
            "delivered_bundle_ids": sorted(self.delivered_bundle_ids),
            "purged_bundle_ids": metrics_snap.get("purged_bundle_ids", []),
            "injected_bundle_count": len(self.injected_bundle_ids),
            "injected_bundle_ids": self.injected_bundle_ids,
            "bundle_timelines": dict(self.bundle_timelines),
            "notes": [
                f"Simulation completed at t={self.clock.end_time}",
                f"{len(store_remaining)} bundles remain in the DTN store.",
            ],
            "bundles_forwarded_total": metrics_snap.get("bundles_forwarded_total", {}),
            "bundles_delivered_total": metrics_snap.get("bundles_delivered_total", {}),
            "bundles_stored_total": metrics_snap.get("bundles_stored_total", {}),
            "bundles_expired_total": metrics_snap.get("bundles_expired_total", {}),
            "recent_purged_ids": metrics_snap.get("recent_purged_ids", []),
            "queue_depths": metrics_snap.get("queue_depths", {}),
            "last_queue_depths": metrics_snap.get("last_queue_depths", {}),
        }
        return report
    
    def build_final_report(self) -> Dict[str, Any]:
        store_remaining = sorted(self.store.list_bundle_ids())
        metrics_snap = self.metrics.snapshot()

        # Wave-18: Compute additive network pressure metrics
        network_metrics = {
            "store_depth_final": compute_store_depth_final(self.store),
            "queue_depth_final": compute_queue_depth_final(self.lunar_queue, self.relay_queue),
            "link_utilization": compute_link_utilization(
                self.contact_manager.contacts, 
                self.capacity_manager
            )
        }

        report = {
            "scenario_name": self.scenario_name,
            "simulation_start_time": self.clock.start_time,
            "simulation_end_time": self.clock.end_time,
            "tick_size": self.clock.tick_size,
            "final_metrics": metrics_snap,
            "network_metrics": network_metrics, # Wave-18 Additive Field
            "store_bundle_ids_remaining": store_remaining,
            "delivered_bundle_ids": sorted(self.delivered_bundle_ids),
            "purged_bundle_ids": metrics_snap.get("purged_bundle_ids", []),
            "injected_bundle_count": len(self.injected_bundle_ids),
            "injected_bundle_ids": self.injected_bundle_ids,
            "bundle_timelines": dict(self.bundle_timelines),
            "notes": [
                f"Simulation completed at t={self.clock.end_time}",
                f"{len(store_remaining)} bundles remain in the DTN store.",
            ],
            "bundles_forwarded_total": metrics_snap.get("bundles_forwarded_total", {}),
            "bundles_delivered_total": metrics_snap.get("bundles_delivered_total", {}),
            "bundles_stored_total": metrics_snap.get("bundles_stored_total", {}),
            "bundles_expired_total": metrics_snap.get("bundles_expired_total", {}),
            "recent_purged_ids": metrics_snap.get("recent_purged_ids", []),
            "queue_depths": metrics_snap.get("queue_depths", {}),
            "last_queue_depths": metrics_snap.get("last_queue_depths", {}),
        }
        return report
    


def create_default_simulator(
    plan_path: str,
    store_dir: str,
    scenario_name: str = "custom",
    inject_short_lived: bool = False,
    tick_size: int = 1,
    simulation_end_override: Optional[int] = None,
) -> Tuple[Simulator, List[Bundle]]:
    cm = ContactManager(plan_path)
    router_app = AetherRouter(cm)
    end_time = simulation_end_override if simulation_end_override is not None else cm.simulation_duration_sec
    clock = SimulationClock(start_time=0, end_time=end_time, tick_size=tick_size)

    lunar_queue = StrictPriorityQueue()
    relay_queue = StrictPriorityQueue()
    metrics = MetricsCollector()
    store = DTNStore(store_dir)

    demo_bundles = [
        Bundle(
            id="tel-001",
            type="telemetry",
            source="lunar-node",
            destination="ground-station",
            priority=classify_bundle("telemetry"),
            created_at=0,
            ttl_sec=3600,
            size_bytes=100,
            payload_ref="payloads/telemetry/tel-001.json",
        ),
        Bundle(
            id="tel-002",
            type="telemetry",
            source="lunar-node",
            destination="ground-station",
            priority=classify_bundle("telemetry"),
            created_at=0,
            ttl_sec=3600,
            size_bytes=100,
            payload_ref="payloads/telemetry/tel-002.json",
        ),
        Bundle(
            id="sci-001",
            type="science",
            source="lunar-node",
            destination="ground-station",
            priority=classify_bundle("science"),
            created_at=0,
            ttl_sec=86400,
            size_bytes=5000,
            payload_ref="payloads/science/sci-001.json",
        ),
    ]

    if inject_short_lived:
        demo_bundles.append(
            Bundle(
                id="tel-short",
                type="telemetry",
                source="lunar-node",
                destination="ground-station",
                priority=classify_bundle("telemetry"),
                created_at=0,
                ttl_sec=10,
                size_bytes=50,
                payload_ref="payloads/telemetry/tel-short.json",
            )
        )

    for bundle in demo_bundles:
        lunar_queue.enqueue(bundle)
        store.save_bundle(bundle)

    sim = Simulator(
        router_app,
        store,
        lunar_queue,
        relay_queue,
        clock,
        metrics,
        scenario_name=scenario_name,
        injected_bundle_ids=[b.id for b in demo_bundles],
    )
    return sim, demo_bundles


def main() -> None:
    parser = argparse.ArgumentParser(description="AetherNet Multi-hop Simulator")
    parser.add_argument("--scenario", type=str, default="default_multihop", help="Built-in scenario profile name")
    parser.add_argument("--report-out", type=str, help="Path to save the final JSON report")
    parser.add_argument("--tick-size", type=int, default=1, help="Simulation tick size in seconds")
    parser.add_argument("--end-time", type=int, help="Override simulation end time")
    args = parser.parse_args()

    try:
        profile = get_scenario(args.scenario)
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(2)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(profile.generate_plan(), plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            simulator, _ = create_default_simulator(
                plan_path=str(plan_path),
                store_dir=tmpstore,
                scenario_name=profile.name,
                inject_short_lived=profile.inject_short_lived_bundle,
                tick_size=args.tick_size,
                simulation_end_override=args.end_time,
            )

            print(f"🚀 Starting AetherNet Simulator | Scenario: {args.scenario}\n")
            report = simulator.run()
            print("\n📊 Simulation Completed.")

            if args.report_out:
                out_path = write_json_report(report, args.report_out)
                print(f"📄 Final report saved to: {out_path}")
            else:
                print("Final Metrics Snapshot:")
                print(json.dumps(report.get("final_metrics", {}), indent=2))
            network_metrics = report.get("network_metrics")
            if network_metrics is not None:
                print("\nNetwork Metrics:")
                print(json.dumps(network_metrics, indent=2))
    finally:
        if plan_path.exists():
            plan_path.unlink()


if __name__ == "__main__":
    main()