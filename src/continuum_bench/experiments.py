"""Compatibility import for :mod:`continuum_bench.monitoring.experiments`."""
import sys
from .monitoring import experiments as _implementation
sys.modules[__name__] = _implementation
