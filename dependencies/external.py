import random

class ExternalDependencyError(Exception):
    pass

def call_external_dependency(target: str, payload: dict) -> bool:
    """
    Simulates a call to an external service.
    Fails on specific payloads or randomly.
    """
    # Deterministic failure via payload flag for automated testing
    if payload.get("force_dependency_failure"):
        raise ExternalDependencyError(f"Simulated failure from {target}")
    
    # Random failure 20% of the time, to demonstrate retry resilience implicitly if needed
    # but we will rely mostly on deterministic failure to avoid flaky tests.
    
    # If a specific target returns specific info:
    if target == "background_check_service":
        if payload.get("applicant_name") == "John Doe Criminal":
            return False # Business failure (Reject)
        return True # Business success

    return True
