"""Compatibility import for :mod:`continuum_bench.monitoring.load_benchmark`."""
import sys
from .monitoring import load_benchmark as _implementation
sys.modules[__name__] = _implementation
