"""Compatibility import for monitoring study placement."""
import sys
from ..monitoring.study import placement as _implementation
sys.modules[__name__] = _implementation
