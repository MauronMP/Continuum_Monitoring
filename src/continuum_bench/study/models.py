"""Compatibility import for monitoring study models."""
import sys
from ..monitoring.study import models as _implementation
sys.modules[__name__] = _implementation
