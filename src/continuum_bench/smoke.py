"""Compatibility import for :mod:`continuum_bench.monitoring.smoke`."""
import sys
from .monitoring import smoke as _implementation
sys.modules[__name__] = _implementation
