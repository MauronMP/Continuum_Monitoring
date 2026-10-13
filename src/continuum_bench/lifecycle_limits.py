"""Finite connectivity budgets, independent of experimental timing limits."""
import math
import os


def connectivity_timeout(name: str, default: float) -> float:
    value = float(os.environ.get(name, default))
    if not math.isfinite(value) or not 1 <= value <= 600:
        raise ValueError(f"{name} must be a finite number between 1 and 600 seconds")
    return value


def ssh_probe_timeout() -> float:
    return connectivity_timeout("CONTINUUM_SSH_PROBE_TIMEOUT_SECONDS", 60)


def health_timeout() -> float:
    return connectivity_timeout("CONTINUUM_HEALTH_TIMEOUT_SECONDS", 10)
