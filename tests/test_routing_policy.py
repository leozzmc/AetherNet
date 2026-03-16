import json

import pytest

from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_graph import ContactForecast
from router.contact_manager import ContactManager
from router.route_scoring import RouteCandidate, RouteScorer
from router.routing_policies import (
    CGRLiteRoutingPolicy,
    ContactAwareRoutingPolicy,
    LegacyRoutingPolicy,
    OpportunisticRoutingPolicy,
    ScoredContactAwareRoutingPolicy,
    StaticRoutingPolicy,
)
from routing.routing_table import RoutingTable


def make_bundle(destination: str = "ground-station", next_hop: str | None = None) -> Bundle:
    return Bundle(
        id="tel-001",
        type="telemetry",
        source="lunar-node",
        destination=destination,
        priority=100,
        created_at=0,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="demo",
        next_hop=next_hop,
    )


def make_contact_manager(tmp_path, contacts=None):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "simulation_duration_sec": 1000,
                "contacts": contacts or [],
            }
        ),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


# --- Wave-37 Legacy and Basic Compatibility Tests ---


def test_legacy_policy_preserves_original_static_route():
    policy = LegacyRoutingPolicy()

    next_hop = policy.select_next_hop(
        current_node="lunar-node",
        bundle=make_bundle(destination="ground-station"),
        current_time=10,
    )

    assert next_hop == "leo-relay"


def test_static_policy_uses_routing_table_with_current_node_context():
    policy = StaticRoutingPolicy(
        RoutingTable(
            {
                "lunar-node": {"ground-station": "relay-a"},
                "relay-a": {"ground-station": "relay-b"},
            }
        )
    )

    first_hop = policy.select_next_hop(
        current_node="lunar-node",
        bundle=make_bundle(destination="ground-station"),
        current_time=10,
    )
    second_hop = policy.select_next_hop(
        current_node="relay-a",
        bundle=make_bundle(destination="ground-station"),
        current_time=11,
    )

    assert first_hop == "relay-a"
    assert second_hop == "relay-b"


def test_router_defaults_to_legacy_policy_when_nothing_is_injected(tmp_path):
    router = AetherRouter(contact_manager=make_contact_manager(tmp_path))

    assert router.get_next_hop("lunar-node", "ground-station") == "leo-relay"


def test_router_uses_static_policy_implicitly_when_routing_table_is_provided(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
    )

    assert router.get_next_hop("node-A", "node-C") == "node-B"


def test_router_accepts_explicit_policy_override_over_routing_table(tmp_path):
    class NullPolicy:
        def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> str | None:
            return None

    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
        routing_policy=NullPolicy(),
    )

    assert router.get_next_hop("node-A", "node-C") is None


def test_can_forward_is_deterministic_when_policy_returns_none(tmp_path):
    class NullPolicy:
        def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> str | None:
            return None

    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        routing_policy=NullPolicy(),
    )

    assert router.can_forward("lunar-node", make_bundle(), current_time=3) is False


# --- Wave-38 Static Routing Baseline Tests ---


def test_static_policy_returns_none_at_destination():
    policy = StaticRoutingPolicy(RoutingTable({"ground-station": {"other": "relay"}}))
    bundle = make_bundle(destination="ground-station")

    assert policy.select_next_hop("ground-station", bundle, 0) is None


def test_static_policy_returns_none_for_unknown_destination():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"known-dest": "relay"}}))
    bundle = make_bundle(destination="unknown-dest")

    assert policy.select_next_hop("lunar-node", bundle, 0) is None


def test_static_policy_returns_none_for_unknown_source():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"ground-station": "relay"}}))
    bundle = make_bundle(destination="ground-station")

    assert policy.select_next_hop("unknown-node", bundle, 0) is None


def test_static_policy_honors_explicit_bundle_next_hop_override():
    policy = StaticRoutingPolicy(RoutingTable({"lunar-node": {"ground-station": "standard-relay"}}))
    bundle = make_bundle(destination="ground-station", next_hop="emergency-relay")

    assert policy.select_next_hop("lunar-node", bundle, 0) == "emergency-relay"


def test_router_can_forward_true_when_static_route_and_contact_exist(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(
            tmp_path,
            contacts=[
                {
                    "source": "node-A",
                    "target": "node-B",
                    "start_time": 0,
                    "end_time": 10,
                    "one_way_delay_ms": 10,
                    "bandwidth_kbit": 100,
                    "bidirectional": False,
                }
            ],
        ),
        routing_table=RoutingTable({"node-A": {"node-C": "node-B"}}),
    )

    bundle = Bundle(
        id="bundle-1",
        type="telemetry",
        source="node-A",
        destination="node-C",
        priority=10,
        created_at=0,
        ttl_sec=100,
        size_bytes=100,
        payload_ref="demo",
    )

    assert router.can_forward("node-A", bundle, current_time=5) is True


def test_router_can_forward_returns_false_at_destination_even_if_contact_exists(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(
            tmp_path,
            contacts=[
                {
                    "source": "ground-station",
                    "target": "relay",
                    "start_time": 0,
                    "end_time": 10,
                    "one_way_delay_ms": 10,
                    "bandwidth_kbit": 100,
                    "bidirectional": False,
                }
            ],
        ),
        routing_table=RoutingTable({"ground-station": {"mars": "relay"}}),
    )
    bundle = make_bundle(destination="ground-station")

    assert router.can_forward("ground-station", bundle, current_time=5) is False


# --- Wave-39 Contact-Aware Routing Policy Tests ---


@pytest.fixture
def wave39_routing_table():
    return RoutingTable({"node-A": {"node-C": "node-B"}})


@pytest.fixture
def wave39_contact_manager(tmp_path):
    return make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "node-B",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            }
        ],
    )


def test_contact_aware_policy_returns_hop_when_open(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=15) == "node-B"


def test_contact_aware_policy_returns_none_when_closed(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=5) is None


def test_contact_aware_policy_returns_none_if_no_route(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="unknown-dest")

    assert policy.select_next_hop("node-A", bundle, current_time=15) is None


def test_contact_aware_policy_returns_none_at_destination(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="node-A")

    assert policy.select_next_hop("node-A", bundle, current_time=15) is None


def test_contact_aware_policy_honors_explicit_override_only_if_open(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="node-C", next_hop="node-B")

    assert policy.select_next_hop("node-A", bundle, current_time=15) == "node-B"
    assert policy.select_next_hop("node-A", bundle, current_time=5) is None


def test_contact_aware_policy_is_deterministic_for_same_time(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    bundle = make_bundle(destination="node-C")

    result_1 = policy.select_next_hop("node-A", bundle, current_time=15)
    result_2 = policy.select_next_hop("node-A", bundle, current_time=15)

    assert result_1 == "node-B"
    assert result_2 == "node-B"


def test_aether_router_can_use_contact_aware_policy_explicitly(wave39_routing_table, wave39_contact_manager):
    policy = ContactAwareRoutingPolicy(wave39_routing_table, wave39_contact_manager)
    router = AetherRouter(
        contact_manager=wave39_contact_manager,
        routing_table=wave39_routing_table,
        routing_policy=policy,
    )

    assert router.get_next_hop("node-A", "node-C", current_time=15) == "node-B"
    assert router.get_next_hop("node-A", "node-C", current_time=5) is None

    bundle = make_bundle(destination="node-C")
    assert router.can_forward("node-A", bundle, current_time=15) is True
    assert router.can_forward("node-A", bundle, current_time=5) is False


# --- Wave-40 Route Scoring Engine & Scored Routing Policy Tests ---


def test_route_scorer_chooses_highest_score():
    candidates = [
        RouteCandidate("relay-1", 10),
        RouteCandidate("relay-2", 50),
        RouteCandidate("relay-3", 5),
    ]
    assert RouteScorer.choose_best(candidates) == "relay-2"


def test_route_scorer_tie_breaks_lexically():
    candidates = [
        RouteCandidate("relay-B", 50),
        RouteCandidate("relay-A", 50),
    ]
    assert RouteScorer.choose_best(candidates) == "relay-A"


def test_route_scorer_returns_none_for_empty_list():
    assert RouteScorer.choose_best([]) is None


@pytest.fixture
def wave40_contact_manager(tmp_path):
    return make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "relay-slow",
                "start_time": 0,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-fast",
                "start_time": 50,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-tie1",
                "start_time": 0,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 50,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-tie2",
                "start_time": 0,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 50,
                "bidirectional": False,
            },
        ],
    )


@pytest.fixture
def wave40_candidates():
    return {
        "node-A": {
            "node-C": [
                RouteCandidate("relay-slow", score=10),
                RouteCandidate("relay-fast", score=90),
                RouteCandidate("relay-tie1", score=50),
                RouteCandidate("relay-tie2", score=50),
            ]
        }
    }


def test_scored_policy_filters_closed_contacts_and_picks_best(wave40_candidates, wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy(wave40_candidates, wave40_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=20) == "relay-tie1"
    assert policy.select_next_hop("node-A", bundle, current_time=60) == "relay-fast"


def test_scored_policy_returns_none_if_no_candidates_available(wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy({}, wave40_contact_manager)

    assert policy.select_next_hop("node-A", make_bundle(destination="node-C"), current_time=20) is None


def test_scored_policy_returns_none_when_all_candidates_are_closed(tmp_path):
    contact_manager = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "relay-closed-1",
                "start_time": 50,
                "end_time": 60,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 50,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-closed-2",
                "start_time": 50,
                "end_time": 60,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 50,
                "bidirectional": False,
            },
        ],
    )

    candidates = {
        "node-A": {
            "node-C": [
                RouteCandidate("relay-closed-1", score=10),
                RouteCandidate("relay-closed-2", score=20),
            ]
        }
    }

    policy = ScoredContactAwareRoutingPolicy(candidates, contact_manager)

    assert policy.select_next_hop("node-A", make_bundle(destination="node-C"), current_time=10) is None


def test_scored_policy_returns_none_at_destination(wave40_candidates, wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy(wave40_candidates, wave40_contact_manager)

    assert policy.select_next_hop("node-C", make_bundle(destination="node-C"), current_time=60) is None


def test_scored_policy_honors_explicit_bundle_override_only_if_open(wave40_candidates, wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy(wave40_candidates, wave40_contact_manager)
    bundle = make_bundle(destination="node-C", next_hop="relay-fast")

    assert policy.select_next_hop("node-A", bundle, current_time=20) is None
    assert policy.select_next_hop("node-A", bundle, current_time=60) == "relay-fast"


def test_scored_policy_is_deterministic_for_same_time(wave40_candidates, wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy(wave40_candidates, wave40_contact_manager)
    bundle = make_bundle(destination="node-C")

    result_1 = policy.select_next_hop("node-A", bundle, current_time=20)
    result_2 = policy.select_next_hop("node-A", bundle, current_time=20)

    assert result_1 == "relay-tie1"
    assert result_2 == "relay-tie1"


def test_aether_router_can_use_scored_policy_explicitly(wave40_candidates, wave40_contact_manager):
    policy = ScoredContactAwareRoutingPolicy(wave40_candidates, wave40_contact_manager)
    router = AetherRouter(
        contact_manager=wave40_contact_manager,
        routing_policy=policy,
    )

    assert router.get_next_hop("node-A", "node-C", current_time=20) == "relay-tie1"
    assert router.get_next_hop("node-A", "node-C", current_time=60) == "relay-fast"

    bundle = make_bundle(destination="node-C")
    assert router.can_forward("node-A", bundle, current_time=20) is True
    assert router.can_forward("node-A", bundle, current_time=60) is True


# --- Wave-41 Contact Forecast + CGR-lite Tests ---


def test_contact_forecast_finds_currently_open_contact(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "A",
                "target": "B",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            }
        ],
    )
    forecast = ContactForecast(cm)

    opp = forecast.find_next_contact("A", "B", after_time=15)

    assert opp is not None
    assert opp.start_time == 15
    assert opp.estimated_arrival_time == 16


def test_contact_forecast_supports_bidirectional_contacts(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "A",
                "target": "B",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 100,
                "bidirectional": True,
            }
        ],
    )
    forecast = ContactForecast(cm)

    opp = forecast.find_next_contact("B", "A", after_time=12)

    assert opp is not None
    assert opp.start_time == 12
    assert opp.estimated_arrival_time == 12


@pytest.fixture
def wave41_contact_manager(tmp_path):
    return make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "node-C",
                "start_time": 80,
                "end_time": 100,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-1",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "relay-1",
                "target": "node-C",
                "start_time": 90,
                "end_time": 100,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-2",
                "start_time": 30,
                "end_time": 40,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "relay-2",
                "target": "node-C",
                "start_time": 45,
                "end_time": 60,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-dead",
                "start_time": 5,
                "end_time": 100,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    )


@pytest.fixture
def wave41_candidates():
    return {
        "node-A": {
            "node-C": [
                RouteCandidate("node-C", score=0),
                RouteCandidate("relay-1", score=0),
                RouteCandidate("relay-2", score=0),
                RouteCandidate("relay-dead", score=0),
            ]
        }
    }


def test_cgr_lite_selects_fastest_overall_path_even_if_closed_now(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=0) == "relay-2"


def test_cgr_lite_prefers_direct_candidate_when_it_arrives_earlier(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "S",
                "target": "D",
                "start_time": 20,
                "end_time": 30,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "S",
                "target": "R",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "R",
                "target": "D",
                "start_time": 50,
                "end_time": 60,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    )
    candidates = {"S": {"D": [RouteCandidate("D"), RouteCandidate("R")]}}
    policy = CGRLiteRoutingPolicy(candidates, cm)

    assert policy.select_next_hop("S", make_bundle(destination="D"), current_time=0) == "D"


def test_cgr_lite_ignores_candidates_with_no_future_first_hop_contact(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "S",
                "target": "good-relay",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "good-relay",
                "target": "D",
                "start_time": 30,
                "end_time": 40,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    )
    candidates = {
        "S": {
            "D": [
                RouteCandidate("missing-relay"),
                RouteCandidate("good-relay"),
            ]
        }
    }
    policy = CGRLiteRoutingPolicy(candidates, cm)

    assert policy.select_next_hop("S", make_bundle(destination="D"), current_time=0) == "good-relay"


def test_cgr_lite_ignores_candidates_with_no_future_second_hop_contact(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=0) != "relay-dead"


def test_cgr_lite_returns_direct_path_when_other_relays_are_no_longer_viable(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    bundle = make_bundle(destination="node-C")

    assert policy.select_next_hop("node-A", bundle, current_time=75) == "node-C"


def test_cgr_lite_lexical_tie_break(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "S",
                "target": "B",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
            {
                "source": "S",
                "target": "A",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
            {
                "source": "B",
                "target": "D",
                "start_time": 30,
                "end_time": 40,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
            {
                "source": "A",
                "target": "D",
                "start_time": 30,
                "end_time": 40,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
        ],
    )
    candidates = {"S": {"D": [RouteCandidate("B"), RouteCandidate("A")]}}
    policy = CGRLiteRoutingPolicy(candidates, cm)

    assert policy.select_next_hop("S", make_bundle(destination="D"), current_time=0) == "A"


def test_cgr_lite_returns_none_at_destination(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)

    assert policy.select_next_hop("node-C", make_bundle(destination="node-C"), current_time=0) is None


def test_cgr_lite_explicit_override_only_works_when_contact_is_open(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    bundle = make_bundle(destination="node-C", next_hop="relay-2")

    assert policy.select_next_hop("node-A", bundle, current_time=0) is None
    assert policy.select_next_hop("node-A", bundle, current_time=30) == "relay-2"


def test_cgr_lite_is_deterministic_for_same_time(wave41_candidates, wave41_contact_manager):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    bundle = make_bundle(destination="node-C")

    result_1 = policy.select_next_hop("node-A", bundle, current_time=0)
    result_2 = policy.select_next_hop("node-A", bundle, current_time=0)

    assert result_1 == "relay-2"
    assert result_2 == "relay-2"


def test_router_integration_with_cgr_lite_separates_preference_from_forwarding(
    wave41_candidates,
    wave41_contact_manager,
):
    policy = CGRLiteRoutingPolicy(wave41_candidates, wave41_contact_manager)
    router = AetherRouter(contact_manager=wave41_contact_manager, routing_policy=policy)
    bundle = make_bundle(destination="node-C")

    assert router.get_next_hop("node-A", "node-C", current_time=0) == "relay-2"
    assert router.can_forward("node-A", bundle, current_time=0) is False
    assert router.can_forward("node-A", bundle, current_time=30) is True


# --- Wave-46 Opportunistic Routing Tests ---


@pytest.fixture
def wave46_contact_manager(tmp_path):
    return make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "relay-low",
                "start_time": 0,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-high-soon",
                "start_time": 15,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-high-late",
                "start_time": 50,
                "end_time": 100,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
        ],
    )


@pytest.fixture
def wave46_candidates():
    return {
        "node-A": {
            "node-B": [
                RouteCandidate("relay-low", score=10),
                RouteCandidate("relay-high-soon", score=50),
                RouteCandidate("relay-high-late", score=90),
            ]
        }
    }


def test_opportunistic_policy_holds_for_better_near_future_contact(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager, hold_window=20)
    bundle = make_bundle(destination="node-B")

    decision = policy.evaluate_decision("node-A", bundle, current_time=0)

    assert decision.reason == "hold_for_better_contact"
    assert decision.next_hop is None


def test_opportunistic_policy_forwards_now_if_better_contact_is_too_late(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager, hold_window=10)
    bundle = make_bundle(destination="node-B")

    decision = policy.evaluate_decision("node-A", bundle, current_time=0)

    assert decision.reason == "selected_opportunistic_now"
    assert decision.next_hop == "relay-low"


def test_opportunistic_policy_forwards_now_if_no_better_future_exists(tmp_path):
    cm = make_contact_manager(
        tmp_path,
        contacts=[
            {
                "source": "node-A",
                "target": "relay-high",
                "start_time": 0,
                "end_time": 100,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            },
            {
                "source": "node-A",
                "target": "relay-low",
                "start_time": 10,
                "end_time": 100,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
                "bidirectional": False,
            },
        ],
    )
    candidates = {
        "node-A": {
            "node-B": [
                RouteCandidate("relay-high", score=90),
                RouteCandidate("relay-low", score=10),
            ]
        }
    }

    policy = OpportunisticRoutingPolicy(candidates, cm, hold_window=20)
    decision = policy.evaluate_decision("node-A", make_bundle(destination="node-B"), current_time=0)

    assert decision.reason == "selected_opportunistic_now"
    assert decision.next_hop == "relay-high"


def test_opportunistic_policy_returns_none_at_destination(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager)
    decision = policy.evaluate_decision("node-B", make_bundle(destination="node-B"), current_time=0)

    assert decision.reason == "at_destination"
    assert decision.next_hop is None


def test_opportunistic_policy_honors_explicit_override_only_when_open(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager, hold_window=20)
    bundle = make_bundle(destination="node-B", next_hop="relay-high-soon")

    decision = policy.evaluate_decision("node-A", bundle, current_time=0)
    assert decision.reason == "explicit_override_blocked"
    assert decision.next_hop is None

    decision = policy.evaluate_decision("node-A", bundle, current_time=20)
    assert decision.reason == "explicit_override_open"
    assert decision.next_hop == "relay-high-soon"


def test_opportunistic_policy_is_deterministic_for_repeated_calls(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager, hold_window=20)
    bundle = make_bundle(destination="node-B")

    decision_1 = policy.evaluate_decision("node-A", bundle, current_time=0)
    decision_2 = policy.evaluate_decision("node-A", bundle, current_time=0)

    assert decision_1.reason == decision_2.reason
    assert decision_1.next_hop == decision_2.next_hop


def test_router_integration_with_opportunistic_policy_holds_then_forwards(wave46_candidates, wave46_contact_manager):
    policy = OpportunisticRoutingPolicy(wave46_candidates, wave46_contact_manager, hold_window=20)
    router = AetherRouter(contact_manager=wave46_contact_manager, routing_policy=policy)
    bundle = make_bundle(destination="node-B")

    decision_now = policy.evaluate_decision("node-A", bundle, current_time=0)
    assert decision_now.reason == "hold_for_better_contact"
    assert router.get_next_hop("node-A", "node-B", current_time=0) is None
    assert router.can_forward("node-A", bundle, current_time=0) is False

    decision_later = policy.evaluate_decision("node-A", bundle, current_time=15)
    assert decision_later.reason == "selected_opportunistic_now"
    assert router.get_next_hop("node-A", "node-B", current_time=15) == "relay-high-soon"
    assert router.can_forward("node-A", bundle, current_time=15) is True