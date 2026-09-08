"""Compatibility import for :mod:`continuum_bench.monitoring.distributed`."""
import sys
from .monitoring import distributed as _implementation
sys.modules[__name__] = _implementation
