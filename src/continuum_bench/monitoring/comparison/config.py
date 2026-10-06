"""Strict comparison configuration independent of legacy experiment controls."""
from pathlib import Path
import math
import tomllib

from .adapters import STRATEGIES

EXPERIMENTS = ("effectiveness", "adaptation", "scalability", "cumulative")
FIELDS = {"policy_config", "topology", "output", "exclude_nodes", "exclude_resources", "strategies",
          "experiments", "repetitions", "warmup", "seed", "timeout_seconds", "connect_timeout_seconds",
          "multipliers", "events_per_context", "cumulative_cycles"}


def load(path):
    path = Path(path).resolve()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    if set(raw) != {"comparison"}:
        raise ValueError("Expected only a [comparison] table")
    config = raw["comparison"]
    if set(config) != FIELDS:
        raise ValueError(f"Unknown/missing comparison keys: {sorted(set(config) ^ FIELDS)}")
    for key in ("repetitions", "events_per_context", "warmup", "seed"):
        minimum = 0 if key in ("warmup", "seed") else 1
        if type(config[key]) is not int or config[key] < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
    for key in ("timeout_seconds", "connect_timeout_seconds"):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be finite and positive; unlimited is deliberately unsupported")
    for key in ("multipliers", "cumulative_cycles"):
        values = config[key]
        if not isinstance(values, list) or not values or any(type(v) is not int or v < 1 for v in values) or values != sorted(set(values)):
            raise ValueError(f"{key} must be strictly increasing positive integers")
    for key, allowed in (("strategies", STRATEGIES), ("experiments", EXPERIMENTS)):
        values = config[key]
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values) or len(values) != len(set(values)) or set(values) - set(allowed):
            raise ValueError(f"Invalid {key}: {values}")
    for key in ("exclude_nodes", "exclude_resources"):
        if not isinstance(config[key], list) or any(not isinstance(v, str) for v in config[key]):
            raise ValueError(f"{key} must be a list of identifiers")
    for key in ("policy_config", "topology", "output"):
        if not isinstance(config[key], str) or not config[key]:
            raise ValueError(f"{key} must be a non-empty path")
    for key in ("policy_config", "topology"):
        config[key] = str((path.parent / config[key]).resolve())
        if not Path(config[key]).is_file():
            raise ValueError(f"Missing {key}: {config[key]}")
    return config
