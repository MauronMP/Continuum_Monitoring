"""Compatibility import for :mod:`continuum_bench.monitoring.experiment_reporting`."""
import sys
from .monitoring import experiment_reporting as _implementation
sys.modules[__name__] = _implementation
