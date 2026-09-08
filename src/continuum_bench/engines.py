"""Compatibility import for :mod:`continuum_bench.monitoring.engines`."""
import sys
from .monitoring import engines as _implementation
sys.modules[__name__] = _implementation
