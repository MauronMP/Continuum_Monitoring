"""Compatibility import for :mod:`continuum_bench.monitoring.engine_reporting`."""
import sys
from .monitoring import engine_reporting as _implementation
sys.modules[__name__] = _implementation
