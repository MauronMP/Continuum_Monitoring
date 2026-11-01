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
    hosts = tuple(Host(**item) for item in data["hosts"] if item["id"] not in excluded)
    if not hosts:
        raise ValueError("The topology has no active hosts")
    return Topology(str(data["name"]), hosts)
