"""Compatibility import for :mod:`continuum_bench.monitoring.physical`."""
import sys
from .monitoring import physical as _implementation
sys.modules[__name__] = _implementation
