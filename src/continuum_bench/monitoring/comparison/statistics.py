"""Repetition-level uncertainty; events are not independent replicates."""
from __future__ import annotations

import hashlib
import numpy as np

MIN_CI_REPETITIONS = 5
BOOTSTRAP_SAMPLES = 5000


def estimate(values, key=""):
    values = np.asarray(values, dtype=float)
    if not values.size:
        return {"mean": None, "low": None, "high": None, "n": 0}
    if not np.isfinite(values).all():
        raise ValueError("Non-finite measurement in statistical summary")
    result = {"mean": float(values.mean()), "low": None, "high": None, "n": len(values)}
    if len(values) >= MIN_CI_REPETITIONS:
        seed = int.from_bytes(hashlib.sha256(str(key).encode()).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        means = rng.choice(values, (BOOTSTRAP_SAMPLES, len(values)), replace=True).mean(axis=1)
        result["low"], result["high"] = map(float, np.percentile(means, [2.5, 97.5]))
    return result
