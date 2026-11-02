from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class Host:
    id: str
    tier: str
    authority: str
    address: str
    port: int
    local: bool = False

    @property
    def endpoint(self) -> str:
        return f"http://{self.address}:{self.port}"


@dataclass(frozen=True)
class Topology:
    name: str
    hosts: tuple[Host, ...]

    @property
    def fingerprint(self) -> str:
        payload = json.dumps([asdict(host) for host in self.hosts], sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


def load_topology(path: Path, excluded: set[str] | None = None) -> Topology:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    excluded = excluded or set()
    configured = tuple(Host(**item) for item in data["hosts"])
    ids = [host.id for host in configured]
    if len(set(ids)) != len(ids):
        raise ValueError("topology host identifiers must be unique")
    if any(host.tier not in {"cloud", "fog", "mist", "edge"} for host in configured):
        raise ValueError("topology tiers must be cloud, fog, mist, or edge")
    if any(not 1 <= host.port <= 65535 for host in configured):
        raise ValueError("topology ports must be between 1 and 65535")
    if sum(host.local for host in configured) > 1:
        raise ValueError("the topology may define at most one local host")
    unknown = excluded - set(ids)
    if unknown:
        raise ValueError(f"unknown excluded hosts: {sorted(unknown)}")
    hosts = tuple(host for host in configured if host.id not in excluded)
    if not hosts:
        raise ValueError("The topology has no active hosts")
    return Topology(str(data["name"]), hosts)
