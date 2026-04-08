from typing import Callable, Dict, List

from aether_scenarios import ScenarioSpec


class Phase6ScenarioRegistry:
    """
    Deterministic registry for canonical Phase-6 demo scenarios.

    This registry provides stable ScenarioSpec factories that can be used by
    demo entrypoints and later Phase-6 integration waves.
    """

    SCENARIO_CLEAN = "clean_baseline_phase6"
    SCENARIO_DEGRADED = "degraded_network_phase6"
    SCENARIO_JAMMED = "jammed_link_phase6"
    SCENARIO_MIXED = "mixed_risk_phase6"

    SEED_CLEAN = 10001
    SEED_DEGRADED = 10002
    SEED_JAMMED = 10003
    SEED_MIXED = 10004

    DEFAULT_NODE_COUNT = 10
    DEFAULT_LINK_COUNT = 20
    DEFAULT_TIME_HORIZON = 100

    _FACTORY: Dict[str, Callable[[], ScenarioSpec]] = {}

    @classmethod
    def _register(cls) -> None:
        if cls._FACTORY:
            return

        cls._FACTORY = {
            cls.SCENARIO_CLEAN: cls._build_clean_baseline,
            cls.SCENARIO_DEGRADED: cls._build_degraded_network,
            cls.SCENARIO_JAMMED: cls._build_jammed_link,
            cls.SCENARIO_MIXED: cls._build_mixed_risk,
        }

    @classmethod
    def _build_clean_baseline(cls) -> ScenarioSpec:
        return ScenarioSpec(
            scenario_name=cls.SCENARIO_CLEAN,
            master_seed=cls.SEED_CLEAN,
            node_count=cls.DEFAULT_NODE_COUNT,
            link_count=cls.DEFAULT_LINK_COUNT,
            time_horizon=cls.DEFAULT_TIME_HORIZON,
            include_reliability_trace=False,
            include_adversarial_trace=False,
            loss_probability=0.0,
            degradation_probability=0.0,
            max_extra_delay_ms=0,
            jamming_probability=0.0,
            malicious_drop_probability=0.0,
            node_compromise_probability=0.0,
            max_injected_delay_ms=0,
        )

    @classmethod
    def _build_degraded_network(cls) -> ScenarioSpec:
        return ScenarioSpec(
            scenario_name=cls.SCENARIO_DEGRADED,
            master_seed=cls.SEED_DEGRADED,
            node_count=cls.DEFAULT_NODE_COUNT,
            link_count=cls.DEFAULT_LINK_COUNT,
            time_horizon=cls.DEFAULT_TIME_HORIZON,
            include_reliability_trace=True,
            include_adversarial_trace=False,
            loss_probability=0.30,
            degradation_probability=0.50,
            max_extra_delay_ms=250,
            jamming_probability=0.0,
            malicious_drop_probability=0.0,
            node_compromise_probability=0.0,
            max_injected_delay_ms=0,
        )

    @classmethod
    def _build_jammed_link(cls) -> ScenarioSpec:
        return ScenarioSpec(
            scenario_name=cls.SCENARIO_JAMMED,
            master_seed=cls.SEED_JAMMED,
            node_count=cls.DEFAULT_NODE_COUNT,
            link_count=cls.DEFAULT_LINK_COUNT,
            time_horizon=cls.DEFAULT_TIME_HORIZON,
            include_reliability_trace=False,
            include_adversarial_trace=True,
            loss_probability=0.0,
            degradation_probability=0.0,
            max_extra_delay_ms=0,
            jamming_probability=0.25,
            malicious_drop_probability=0.20,
            node_compromise_probability=0.10,
            max_injected_delay_ms=500,
        )

    @classmethod
    def _build_mixed_risk(cls) -> ScenarioSpec:
        return ScenarioSpec(
            scenario_name=cls.SCENARIO_MIXED,
            master_seed=cls.SEED_MIXED,
            node_count=cls.DEFAULT_NODE_COUNT,
            link_count=cls.DEFAULT_LINK_COUNT,
            time_horizon=cls.DEFAULT_TIME_HORIZON,
            include_reliability_trace=True,
            include_adversarial_trace=True,
            loss_probability=0.15,
            degradation_probability=0.30,
            max_extra_delay_ms=100,
            jamming_probability=0.15,
            malicious_drop_probability=0.10,
            node_compromise_probability=0.05,
            max_injected_delay_ms=200,
        )

    @classmethod
    def get_all_scenario_names(cls) -> List[str]:
        cls._register()
        return list(cls._FACTORY.keys())

    @classmethod
    def get_spec_by_name(cls, name: str) -> ScenarioSpec:
        cls._register()
        if name not in cls._FACTORY:
            raise ValueError(f"Unknown Phase-6 scenario name: {name}")
        return cls._FACTORY[name]()

    @classmethod
    def get_clean_baseline(cls) -> ScenarioSpec:
        return cls.get_spec_by_name(cls.SCENARIO_CLEAN)

    @classmethod
    def get_degraded_network(cls) -> ScenarioSpec:
        return cls.get_spec_by_name(cls.SCENARIO_DEGRADED)

    @classmethod
    def get_jammed_link(cls) -> ScenarioSpec:
        return cls.get_spec_by_name(cls.SCENARIO_JAMMED)

    @classmethod
    def get_mixed_risk(cls) -> ScenarioSpec:
        return cls.get_spec_by_name(cls.SCENARIO_MIXED)