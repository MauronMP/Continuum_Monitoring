"""Compatibility import for :mod:`continuum_bench.monitoring.experiment_config`."""
import sys
from .monitoring import experiment_config as _implementation
sys.modules[__name__] = _implementation
