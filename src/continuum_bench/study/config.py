"""Compatibility import for monitoring study config."""
import sys
from ..monitoring.study import config as _implementation
sys.modules[__name__] = _implementation
