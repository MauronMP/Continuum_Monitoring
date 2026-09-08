"""Compatibility import for :mod:`continuum_bench.monitoring.load_config`."""
import sys
from .monitoring import load_config as _implementation
sys.modules[__name__] = _implementation
