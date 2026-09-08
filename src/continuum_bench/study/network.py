"""Compatibility import for monitoring study network."""
import sys
from ..monitoring.study import network as _implementation
sys.modules[__name__] = _implementation
