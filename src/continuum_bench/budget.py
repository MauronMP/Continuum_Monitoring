"""Compatibility import for :mod:`continuum_bench.monitoring.budget`."""
import sys
from .monitoring import budget as _implementation
sys.modules[__name__] = _implementation
