"""Compatibility import for :mod:`continuum_bench.monitoring.benchmark`."""
import sys
from .monitoring import benchmark as _implementation
sys.modules[__name__] = _implementation
