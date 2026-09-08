"""Domain ports with no infrastructure, benchmark or visualization imports."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

TIERS = ("cloud", "fog", "mist", "edge", "iot")

@dataclass(frozen=True)
class Ontology:
    identifier: str
    version: str
    sources: tuple[str, ...]
    digest: str = ""

@dataclass(frozen=True)
class Policy:
    identifier: str
    category: str
    complexity: int = 1
    requirement_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class Requirement:
    identifier: str
    description: str
    policy_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class Query:
    identifier: str
    text: str
    category: str
    complexity: int = 1
    policy_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class ReasoningResult:
    graph: Any
    duration_ms: float
    input_triples: int
    output_triples: int

    @property
    def inferred_triples(self) -> int:
        return self.output_triples - self.input_triples

class Reasoner(Protocol):
    name: str
    def materialize(self, source: Any) -> ReasoningResult: ...

class MetricCollector(Protocol):
    def snapshot(self) -> Mapping[str, float | int | None]: ...

class ResultSink(Protocol):
    def write(self, record: Mapping[str, Any]) -> None: ...

class MobilityModel(Protocol):
    """Future extension port; no trajectory simulation is required by core."""
    def position_at(self, node_id: str, timestamp_seconds: float) -> Any: ...

@dataclass(frozen=True)
class MobilityConfiguration:
    model: str = "static"
    seed: int = 2026
    parameters: Mapping[str, Any] = field(default_factory=dict)
