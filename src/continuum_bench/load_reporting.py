"""Compatibility import for :mod:`continuum_bench.monitoring.load_reporting`."""
import sys
from .monitoring import load_reporting as _implementation
sys.modules[__name__] = _implementation
