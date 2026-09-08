"""Compatibility import for monitoring study workload."""
import sys
from ..monitoring.study import workload as _implementation
sys.modules[__name__] = _implementation
