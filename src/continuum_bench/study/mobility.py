"""Compatibility import for monitoring study mobility."""
import sys
from ..monitoring.study import mobility as _implementation
sys.modules[__name__] = _implementation
