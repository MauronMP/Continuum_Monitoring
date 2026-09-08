"""Compatibility import for monitoring study analysis."""
import sys
from ..monitoring.study import analysis as _implementation
sys.modules[__name__] = _implementation
