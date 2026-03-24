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
from metrics.delivery_metrics import DeliveryMetrics
from sim.scenarios import get_scenario
from sim.reporting import write_json_report
from link.capacity_manager import ContactWindowCapacityManager
from metrics.network_metrics import (
    compute_store_depth_final,
    compute_queue_depth_final,
    compute_link_utilization
)
from node.node_runtime import NodeRuntime
from protocol.reassembly_buffer import ReassemblyBuffer
from protocol.reassembly import can_reassemble, reassemble_bundle
from router.route_scoring import RouteCandidate
from router.routing_policies import StaticRoutingPolicy, ContactAwareRoutingPolicy, MultiPathRoutingPolicy
from routing.routing_table import RoutingTable


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
        extra_queues: Optional[Dict[str, StrictPriorityQueue]] = None,  # Wave-21 Additive parameter
        routing_mode: str = "baseline",
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
        self.routing_mode = routing_mode
        self._contact_log_state: Dict[tuple[str, str], bool] = {}
        self.delivered_bundle_ids: List[str] = []
        self.injected_bundle_ids: List[str] = sorted(injected_bundle_ids or [])
        self.bundle_timelines: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.capacity_manager = ContactWindowCapacityManager()
        self.nodes: Dict[str, NodeRuntime] = {
            "lunar-node": NodeRuntime("lunar-node", self.lunar_queue, role="source"),
            "leo-relay": NodeRuntime("leo-relay", self.relay_queue, role="relay"),
        }
        if extra_queues:
            for node_id, q in extra_queues.items():
                self.nodes[node_id] = NodeRuntime(node_id, q, role="extra_relay")

        # Wave-25: Destination-side reassembly buffers mapped by node_id
        self.reassembly_buffers: Dict[str, ReassemblyBuffer] = {}

    def _get_reassembly_buffer(self, node_id: str) -> ReassemblyBuffer:
        if node_id not in self.reassembly_buffers:
            self.reassembly_buffers[node_id] = ReassemblyBuffer()
        return self.reassembly_buffers[node_id]

    @property
    def node_queues(self) -> Dict[str, StrictPriorityQueue]:
        """
        Backward-compatibility helper property.
        Dynamically projects the self.nodes dict back into a simple {node_id: queue} mapping.
        This ensures existing tick() processing and Wave-21 metrics helpers function flawlessly.
        """
        return {node_id: node.queue for node_id, node in self.nodes.items()}

    def _record_timeline_event(self, bundle_id: str, event_key: str, current_time: int) -> None:
        """Record the first occurrence of a specific lifecycle event for a bundle."""
        if event_key not in self.bundle_timelines[bundle_id]:
            self.bundle_timelines[bundle_id][event_key] = current_time

    def _update_link_logs(self, current_time: int) -> None:
        active_pairs = {(contact.source, contact.target) for contact in self.contact_manager.get_active_contacts(current_time)}
        all_pairs = {(contact.source, contact.target) for contact in self.contact_manager.contacts}

        for source, target in sorted(all_pairs):
            is_active = (source, target) in active_pairs
            was_active = self._contact_log_state.get((source, target), False)

            if is_active and not was_active:
                print(f"[t={current_time:02d}] link up: {source} -> {target}")
            elif was_active and not is_active:
                print(f"[t={current_time:02d}] link down: {source} -> {target}")

            self._contact_log_state[(source, target)] = is_active

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

    def _routing_table_next_hop(self, current_node: str, destination: str) -> Optional[str]:
        routing_table = getattr(self.router, "routing_table", None)
        if routing_table is None:
            return None

        get_next_hop = getattr(routing_table, "get_next_hop", None)
        if callable(get_next_hop):
            return get_next_hop(current_node, destination)

        return None

    def _resolve_next_hop_and_contact(
        self,
        current_node: str,
        destination: str,
        current_time: int,
    ) -> Tuple[Optional[str], Optional[Contact]]:
        next_hop = self.router.get_next_hop(current_node, destination, current_time=current_time)
        if next_hop == current_node:
            next_hop = None

        contact = self._find_matching_contact(current_node, next_hop, current_time)
        if contact is not None:
            if next_hop is None:
                next_hop = contact.target if contact.source == current_node else contact.source
            return next_hop, contact

        fallback_hop = self._routing_table_next_hop(current_node, destination)
        if fallback_hop and fallback_hop != current_node:
            contact = self._find_matching_contact(current_node, fallback_hop, current_time)
            if contact is not None:
                return fallback_hop, contact

        # Baseline mode should remain faithful to the deterministic routing table.
        # If the preferred static next hop is unavailable, baseline waits rather than
        # opportunistically switching to a different active contact.
        if self.routing_mode == "baseline":
            return None, None

        contact = self._find_matching_contact(current_node, None, current_time)
        if contact is not None:
            hop = contact.target if contact.source == current_node else contact.source
            return hop, contact

        return None, None

    def _process_hop(
        self,
        current_node: str,
        outbound_queue: StrictPriorityQueue,
        current_time: int,
    ) -> Tuple[Optional[Bundle], Optional[str]]:
        if outbound_queue.size() == 0:
            return None, None

        bundle = outbound_queue.peek(current_time)
        if bundle is None:
            return None, None

        next_hop, contact = self._resolve_next_hop_and_contact(current_node, bundle.destination, current_time)
        if contact is None or next_hop is None:
            return None, None

        if not self.capacity_manager.can_forward(contact):
            return None, None

        bundle = outbound_queue.dequeue(current_time)
        if bundle is None:
            return None, None

        resolved_next_hop, _ = self._resolve_next_hop_and_contact(current_node, bundle.destination, current_time)
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

        # Wave-21 & Wave-25 Integration: Final hop logic
        if next_hop == bundle.destination:
            if bundle.status != BundleStatus.DELIVERED:
                if bundle.status == BundleStatus.STORED:
                    bundle.transition(BundleStatus.FORWARDING)
                if bundle.status == BundleStatus.FORWARDING:
                    bundle.transition(BundleStatus.DELIVERED)

            # Wave-25: Intercept fragments at destination
            if bundle.is_fragment and bundle.original_bundle_id:
                buffer = self._get_reassembly_buffer(bundle.destination)
                buffer.add(bundle)

                # Check if we have a complete set
                fragment_group = buffer.get(bundle.original_bundle_id)
                if can_reassemble(fragment_group):
                    full_bundle = reassemble_bundle(fragment_group)
                    buffer.remove(bundle.original_bundle_id)

                    # Store and record the reassembled bundle
                    full_bundle.transition(BundleStatus.DELIVERED)
                    self.store.save_bundle(full_bundle)
                    self.metrics.record_delivered(full_bundle.type)
                    self.router.deliver_bundle(full_bundle, current_time)
                    self.delivered_bundle_ids.append(full_bundle.id)
                    self._record_timeline_event(full_bundle.id, "delivered_tick", current_time)
                    print(f"[t={current_time:02d}] REASSEMBLED {full_bundle.id} from fragments at {bundle.destination}")
            else:
                # Normal bundle delivery
                self.metrics.record_delivered(bundle.type)
                self.router.deliver_bundle(bundle, current_time)
                self.delivered_bundle_ids.append(bundle.id)
                self._record_timeline_event(bundle.id, "delivered_tick", current_time)
                print(f"[t={current_time:02d}] {bundle.id} delivered to {bundle.destination}")
        else:
            self.metrics.record_stored(bundle.type)
            self._record_timeline_event(bundle.id, "stored_tick", current_time)
            print(f"[t={current_time:02d}] {bundle.id} stored at {next_hop}")

        return bundle, next_hop

    def tick(self, current_time: int) -> None:
        self._update_link_logs(current_time)
        self._apply_retention(current_time)

        # Predictable topological sort for standard scenarios to allow same-tick multi-hop behaviors.
        # This prevents breaking existing timelines where lunar->relay->ground happens instantly.
        processing_order = ["lunar-node", "relay-a", "relay-b", "leo-relay"]

        # Safely append any unexpected nodes dynamically injected via extra_queues
        for node in self.node_queues:
            if node not in processing_order:
                processing_order.append(node)

        for current_node in processing_order:
            if current_node not in self.node_queues:
                continue

            outbound_queue = self.node_queues[current_node]
            moved_bundle, next_hop = self._process_hop(current_node, outbound_queue, current_time)

            if moved_bundle is not None and moved_bundle.status == BundleStatus.STORED:
                if next_hop is not None and next_hop in self.node_queues:
                    self.node_queues[next_hop].enqueue(moved_bundle)

        # Dynamic metrics tracking
        for node_name, q in self.node_queues.items():
            safe_name = node_name.replace("-", "_")
            self.metrics.set_queue_depth(f"queue_depth_{safe_name}", q.size())

    def run(self) -> Dict[str, Any]:
        for t in self.clock.ticks():
            self.tick(t)
        return self.build_final_report()

    def build_final_report(self) -> Dict[str, Any]:
        metrics_snap = self.metrics.snapshot()
        metrics_snap.update(self.router.delivery_metrics.snapshot())

        delivered_ids = set(self.delivered_bundle_ids)
        purged_ids = set(metrics_snap.get("purged_bundle_ids", []))
        store_remaining = sorted(
            bundle_id
            for bundle_id in self.store.list_bundle_ids()
            if bundle_id not in delivered_ids and bundle_id not in purged_ids
        )

        network_metrics = {
            "store_depth_final": compute_store_depth_final(self.store),
            "queue_depth_final": compute_queue_depth_final(self.node_queues),
            "link_utilization": compute_link_utilization(
                self.contact_manager.contacts,
                self.capacity_manager,
            ),
        }

        report = {
            "scenario_name": self.scenario_name,
            "simulation_start_time": self.clock.start_time,
            "simulation_end_time": self.clock.end_time,
            "tick_size": self.clock.tick_size,
            "final_metrics": metrics_snap,
            "network_metrics": network_metrics,
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
            "bundles_dropped_total": metrics_snap.get("bundles_dropped_total", {}),
            "dropped_bundle_ids": metrics_snap.get("dropped_bundle_ids", []),
            "recent_purged_ids": metrics_snap.get("recent_purged_ids", []),
            "queue_depths": metrics_snap.get("queue_depths", {}),
            "last_queue_depths": metrics_snap.get("last_queue_depths", {}),
            "routing_mode": self.routing_mode,
        }
        return report


def _normalize_routing_mode(routing_mode: Optional[str]) -> str:
    normalized = (routing_mode or "baseline").strip().lower()
    allowed = {"baseline", "contact_aware", "multipath"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported routing_mode '{routing_mode}'. Allowed: {sorted(allowed)}")
    return normalized


def _score_path(path: List[Tuple[str, str, Contact, int]]) -> int:
    latest_start = max(step[2].start_time for step in path)
    total_delay_ms = sum(step[2].one_way_delay_ms for step in path)
    bottleneck_bandwidth = min(step[2].bandwidth_kbit for step in path)
    hop_penalty = len(path) * 100
    return 1_000_000 - (latest_start * 1000) - total_delay_ms - hop_penalty + bottleneck_bandwidth


def _derive_routing_artifacts(contacts: List[Contact]) -> Tuple[RoutingTable, Dict[str, Dict[str, List[RouteCandidate]]]]:
    adjacency: Dict[str, List[Tuple[str, Contact, int]]] = defaultdict(list)
    nodes = set()

    for idx, contact in enumerate(contacts):
        nodes.add(contact.source)
        nodes.add(contact.target)
        adjacency[contact.source].append((contact.target, contact, idx))
        if contact.bidirectional:
            adjacency[contact.target].append((contact.source, contact, idx))

    def enumerate_paths(source: str, destination: str, max_hops: int = 4) -> List[List[Tuple[str, str, Contact, int]]]:
        paths: List[List[Tuple[str, str, Contact, int]]] = []

        def dfs(current: str, visited: set[str], path: List[Tuple[str, str, Contact, int]]) -> None:
            if len(path) > max_hops:
                return
            if current == destination and path:
                paths.append(list(path))
                return
            for neighbor, contact, order in adjacency.get(current, []):
                if neighbor in visited:
                    continue
                path.append((current, neighbor, contact, order))
                dfs(neighbor, visited | {neighbor}, path)
                path.pop()

        dfs(source, {source}, [])
        return paths

    routes: Dict[str, Dict[str, str]] = {}
    candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]] = {}

    for source in sorted(nodes):
        for destination in sorted(nodes):
            if source == destination:
                continue
            paths = enumerate_paths(source, destination)
            if not paths:
                continue

            best_baseline_path = min(
                paths,
                key=lambda path: (tuple(step[3] for step in path), len(path), path[0][1]),
            )
            routes.setdefault(source, {})[destination] = best_baseline_path[0][1]

            best_by_hop: Dict[str, RouteCandidate] = {}
            for path in paths:
                first_hop = path[0][1]
                candidate = RouteCandidate(next_hop=first_hop, score=_score_path(path))
                existing = best_by_hop.get(first_hop)
                if existing is None or candidate.score > existing.score:
                    best_by_hop[first_hop] = candidate

            candidate_routes.setdefault(source, {})[destination] = sorted(
                best_by_hop.values(),
                key=lambda c: (-c.score, c.next_hop),
            )

    return RoutingTable(routes), candidate_routes


def _build_routing_policy(
    routing_mode: str,
    routing_table: RoutingTable,
    candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]],
    contact_manager: ContactManager,
):
    if routing_mode == "baseline":
        return StaticRoutingPolicy(routing_table)
    if routing_mode == "contact_aware":
        return ContactAwareRoutingPolicy(routing_table, contact_manager)
    if routing_mode == "multipath":
        return MultiPathRoutingPolicy(candidate_routes, contact_manager)
    raise ValueError(f"Unsupported routing_mode '{routing_mode}'")


def create_default_simulator(
    plan_path: str,
    store_dir: str,
    scenario_name: str = "custom",
    inject_short_lived: bool = False,
    tick_size: int = 1,
    simulation_end_override: Optional[int] = None,
    routing_mode: Optional[str] = None,
) -> Tuple[Simulator, List[Bundle]]:
    cm = ContactManager(plan_path)
    with Path(plan_path).open("r", encoding="utf-8") as f:
        raw_plan = json.load(f)

    normalized_routing_mode = _normalize_routing_mode(routing_mode or raw_plan.get("routing_mode"))
    routing_table, candidate_routes = _derive_routing_artifacts(cm.contacts)
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

    delivery_metrics = DeliveryMetrics(expected_total_bundles=len(demo_bundles))
    router_policy = _build_routing_policy(
        normalized_routing_mode,
        routing_table,
        candidate_routes,
        cm,
    )
    router_app = AetherRouter(
        cm,
        routing_table=routing_table,
        routing_policy=router_policy,
        delivery_metrics=delivery_metrics,
    )

    intermediate_nodes = sorted({
        node
        for contact in cm.contacts
        for node in (contact.source, contact.target)
        if node not in {"lunar-node", "ground-station", "leo-relay"}
    })
    extra_queues = {node_id: StrictPriorityQueue() for node_id in intermediate_nodes}

    sim = Simulator(
        router_app,
        store,
        lunar_queue,
        relay_queue,
        clock,
        metrics,
        scenario_name=scenario_name,
        injected_bundle_ids=[b.id for b in demo_bundles],
        extra_queues=extra_queues,
        routing_mode=normalized_routing_mode,
    )
    return sim, demo_bundles


def main() -> None:
    parser = argparse.ArgumentParser(description="AetherNet Multi-hop Simulator")
    parser.add_argument("--scenario", type=str, default="default_multihop", help="Built-in scenario profile name")
    parser.add_argument("--report-out", type=str, help="Path to save the final JSON report")
    parser.add_argument("--tick-size", type=int, default=1, help="Simulation tick size in seconds")
    parser.add_argument("--end-time", type=int, help="Override simulation end time")
    parser.add_argument("--routing-mode", type=str, choices=["baseline", "contact_aware", "multipath"], help="Override routing mode")
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
                routing_mode=args.routing_mode or profile.routing_mode,
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