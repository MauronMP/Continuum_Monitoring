"""Compatibility import for monitoring study sparql."""
import sys
from ..monitoring.study import sparql as _implementation
sys.modules[__name__] = _implementation
