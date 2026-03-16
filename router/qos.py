from dataclasses import dataclass
from typing import Optional

from router.bundle import Bundle


@dataclass(frozen=True)
class QoSConfig:
    """
    Wave-44: Immutable configuration for Quality of Service and Priority Aging.
    Defines baseline priorities for differentiated service classes and 
    parameters for deterministic priority aging to prevent starvation.
    """
    # Baseline priorities by service class
    telemetry_priority: int = 100
    science_priority: int = 50
    bulk_priority: int = 10
    
    # Priority aging mechanics
    aging_interval: int = 10     # How many time ticks before an aging step is applied
    aging_step: int = 5          # How much priority is added per interval
    aging_cap: Optional[int] = 200 # Maximum total effective priority (None for no cap)
    
    # If True, the explicit bundle.priority overrides the type-based baseline.
    # If False, the type-based baseline overrides the bundle's intrinsic priority.
    honor_intrinsic_priority: bool = True


class QoSPolicyHelper:
    """
    Wave-44: A pure, deterministic helper for calculating effective bundle priorities.
    Does NOT mutate bundle state.
    """
    
    def __init__(self, config: Optional[QoSConfig] = None):
        self.config = config or QoSConfig()

    def base_priority(self, bundle: Bundle) -> int:
        """
        Determines the baseline priority before any time-based aging is applied.
        """
        if self.config.honor_intrinsic_priority and bundle.priority > 0:
            return bundle.priority

        # Fallback to service class differentiation based on bundle type
        b_type = bundle.type.lower() if bundle.type else ""
        
        if b_type == "telemetry":
            return self.config.telemetry_priority
        elif b_type == "science":
            return self.config.science_priority
        elif b_type == "bulk":
            return self.config.bulk_priority
        
        # Default fallback for unknown types
        return 0

    def effective_priority(self, bundle: Bundle, current_time: int) -> int:
        """
        Calculates the effective priority at a specific simulation time.
        Applies deterministic aging to prevent low-priority starvation.
        """
        base = self.base_priority(bundle)
        
        # Bundles from the future (or exact present) get no aging bonus
        if current_time <= bundle.created_at:
            return base
            
        wait_time = current_time - bundle.created_at
        
        if self.config.aging_interval <= 0:
            aging_bonus = 0
        else:
            aging_steps = wait_time // self.config.aging_interval
            aging_bonus = aging_steps * self.config.aging_step

        effective_pri = base + aging_bonus
        
        if self.config.aging_cap is not None:
            effective_pri = min(effective_pri, self.config.aging_cap)
            
        return effective_pri