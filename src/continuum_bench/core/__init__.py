"""Shared domain model for physical continuum ontology monitoring."""

from .domain import (
    GeographicPosition,
    NodeCapacity,
    NodeDynamicState,
    PhysicalContinuumNode,
    ReasonerConfiguration,
)

__all__ = [
    "GeographicPosition",
    "NodeCapacity",
    "NodeDynamicState",
    "PhysicalContinuumNode",
    "ReasonerConfiguration",
]

from .contracts import (Ontology, Policy, Requirement, Query, Reasoner,
    ReasoningResult, MetricCollector, ResultSink, MobilityModel, MobilityConfiguration)
from .domain import PhysicalContinuum
