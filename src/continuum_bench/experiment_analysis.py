"""Compatibility import for :mod:`continuum_bench.monitoring.experiment_analysis`."""
import sys
from .monitoring import experiment_analysis as _implementation
sys.modules[__name__] = _implementation
