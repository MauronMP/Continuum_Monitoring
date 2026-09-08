"""Compatibility import for :mod:`continuum_bench.monitoring.config`."""
import sys
from .monitoring import config as _implementation
sys.modules[__name__] = _implementation
