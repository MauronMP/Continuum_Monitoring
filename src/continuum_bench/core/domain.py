"""Reusable physical-continuum domain concepts.

The core package is intentionally free of benchmark orchestration. It models
the entities shared by ontology, policy, requirement, query and reasoner
workflows so that future modules can reuse the same vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass

import math
from .contracts import TIERS


@dataclass(frozen=True)
class GeographicPosition:
    """Machine-readable location prepared for later mobility experiments."""

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    region: str = ""

    def __post_init__(self) -> None:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be supplied together")
        for value, limit in ((self.latitude, 90), (self.longitude, 180)):
            if value is not None and (not math.isfinite(value) or abs(value) > limit):
                raise ValueError("Geographic coordinates are out of range")
        if self.altitude_m is not None and not math.isfinite(self.altitude_m):
            raise ValueError("Altitude must be finite")

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

    def __post_init__(self) -> None:
        values = (self.cpu_cores, self.ram_mib, self.storage_mib,
                  self.processing_capacity, self.network_mbps)
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("Resource capacities must be finite and nonnegative")
        if self.cpu_cores == 0 or self.ram_mib == 0 or self.processing_capacity == 0:
            raise ValueError("CPU, RAM and processing capacity must be positive")


@dataclass(frozen=True)
class NodeDynamicState:
    """Dynamic resource values sampled during an experiment."""

    cpu_percent: float | None = None
    memory_used_mib: float | None = None
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
    device_type: str = "unknown"
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


@dataclass(frozen=True)
class PhysicalContinuum:
    identifier: str
    nodes: tuple[PhysicalContinuumNode, ...]

    def __post_init__(self) -> None:
        ids = [node.node_id for node in self.nodes]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("A continuum requires unique physical node identifiers")
