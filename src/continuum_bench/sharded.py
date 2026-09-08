"""Compatibility import for :mod:`continuum_bench.monitoring.sharded`."""
import sys
from .monitoring import sharded as _implementation
sys.modules[__name__] = _implementation
