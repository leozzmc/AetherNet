def classify_bundle(bundle_type: str) -> int:
    """
    Maps bundle types to priority levels.
    Higher integer means higher priority.
    """
    priorities = {
        "telemetry": 100,
        "science": 50
    }
    # Default to lowest priority if unknown
    return priorities.get(bundle_type.lower(), 10)