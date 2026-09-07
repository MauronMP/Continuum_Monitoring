"""Reusable physical-continuum domain concepts.

The core package is intentionally free of benchmark orchestration. It models
the entities shared by ontology, policy, requirement, query and reasoner
workflows so that future modules can reuse the same vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..topology import TIERS


@dataclass(frozen=True)
class GeographicPosition:
    """Machine-readable location prepared for later mobility experiments."""

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    region: str = ""

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None


@dataclass(frozen=True)
class NodeCapacity:
    """Static resource capacity advertised by a physical node."""

    cpu_cores: float
    ram_mib: int
    cpu_architecture: str = "unknown"
    storage_mib: int = 0
    processing_capacity: float = 1.0
    network_mbps: float = 0.0


@dataclass(frozen=True)
class NodeDynamicState:
    """Dynamic resource values sampled during an experiment."""

    cpu_percent: float = 0.0
    memory_used_mib: int = 0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0


@dataclass(frozen=True)
class PhysicalContinuumNode:
    """A configured node in the cloud-fog-mist-edge-IoT continuum."""

    node_id: str
    tier: str
    endpoint: str
    host: str
    capacity: NodeCapacity
    location: GeographicPosition = GeographicPosition()
    authority: bool = False
    categories: tuple[str, ...] = ()
    local: bool = False

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"Unsupported continuum tier: {self.tier}")


@dataclass(frozen=True)
class ReasonerConfiguration:
    """Reasoning engine selection independent from experiment definitions."""

    name: str
    profile: str
    owl_fragment: str
    suitable_for_physical_nodes: bool
    notes: str = ""
