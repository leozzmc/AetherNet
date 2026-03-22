from typing import List

from sim.experiment_harness import ExperimentCase

# Wave-61: Static, deterministic registry of canonical baseline profiles.
# Explicit definition is preferred over dynamic discovery to guarantee reproducible research.
_PROFILES = {
    "minimal_baseline": [
        ExperimentCase(
            case_name="minimal_baseline__default_multihop",
            scenario_name="default_multihop",
            tick_size=1,
            simulation_end_override=None
        )
    ],
    "routing_baseline": [
        ExperimentCase(
            case_name="routing_baseline__default_multihop__tick1",
            scenario_name="default_multihop",
            tick_size=1,
            simulation_end_override=None
        ),
        ExperimentCase(
            case_name="routing_baseline__default_multihop__tick5",
            scenario_name="default_multihop",
            tick_size=5,
            simulation_end_override=None
        )
    ],
    "delivery_stress_baseline": [
        ExperimentCase(
            case_name="delivery_stress__delayed_delivery",
            scenario_name="delayed_delivery",
            tick_size=1,
            simulation_end_override=None
        ),
        ExperimentCase(
            case_name="delivery_stress__expiry_before_contact",
            scenario_name="expiry_before_contact",
            tick_size=1,
            simulation_end_override=None
        )
    ]
}


def list_baseline_profiles() -> List[str]:
    """
    Wave-61: Return deterministically ordered baseline profile names.
    """
    return sorted(list(_PROFILES.keys()))


def build_baseline_profile(profile_name: str) -> List[ExperimentCase]:
    """
    Wave-61: Return a deterministically ordered list of ExperimentCase objects
    for the requested baseline profile.
    
    Raises ValueError for unknown profile names.
    """
    if profile_name not in _PROFILES:
        valid_profiles = list_baseline_profiles()
        raise ValueError(
            f"Unknown baseline profile: '{profile_name}'. "
            f"Valid profiles are: {valid_profiles}"
        )
        
    # Return a new list instance to prevent accidental mutation of the registry
    return list(_PROFILES[profile_name])