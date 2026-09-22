"""Public import for the physical distributed ontology coordinator."""
import sys
from .monitoring import distributed_ontology as _implementation
sys.modules[__name__] = _implementation
