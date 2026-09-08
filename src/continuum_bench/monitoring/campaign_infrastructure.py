"""Physical HTTP transport behind an experiment-independent execution port."""
from typing import Protocol
from ..topology import Topology
from .distributed import _request, discover

class Infrastructure(Protocol):
    def inventory(self) -> list[dict]: ...
    def call(self, node: dict, operation: str, payload: dict, timeout: float) -> dict: ...

class PhysicalInfrastructure:
    def __init__(self, topology: Topology):
        self.topology = topology

    def inventory(self):
        discover(self.topology.endpoints(), self.topology.active_nodes, self.topology.fingerprint)
        return [{'node_id': n.node_id, 'endpoint': n.endpoint, 'static': n.public(),
                 'observed': _request(n.endpoint, '/health', timeout=5)}
                for n in self.topology.active_nodes]

    def call(self, node, operation, payload, timeout):
        return _request(node['endpoint'], '/campaign/' + operation,
                        {**payload, 'phase_timeout_seconds': max(0.1, timeout - 1)}, timeout=timeout)
