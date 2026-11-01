from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread
from time import monotonic

from .topology import Host

_UNITS = {"B": 1, "KB": 1000, "MB": 1000**2, "GB": 1000**3, "KIB": 1024, "MIB": 1024**2, "GIB": 1024**3}


def _bytes(value: str) -> int | None:
    match = re.search(r"([0-9.]+)\s*([KMGT]?i?B)", value, re.IGNORECASE)
    return None if not match else int(float(match.group(1)) * _UNITS[match.group(2).upper()])


def _io_pair(value: str) -> tuple[int | None, int | None]:
    parts = value.split("/")
    return (_bytes(parts[0]), _bytes(parts[1])) if len(parts) == 2 else (None, None)


class ResourceSampler:
    def __init__(self, hosts: tuple[Host, ...], ssh_user: str, image: str, output: Path, interval: float):
        self.hosts, self.ssh_user, self.image, self.output, self.interval = hosts, ssh_user, image, output, interval
        self.stop_event = Event()
        self.thread: Thread | None = None

    def __enter__(self):
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=self.interval + 5)

    def _sample(self, host: Host) -> dict:
        command = f"id=$(docker ps --filter ancestor={self.image} -q | head -1); test -n \"$id\" || id=$(docker ps --filter label=com.docker.compose.service=worker -q | head -1); test -n \"$id\" && docker stats --no-stream --format '{{{{json .}}}}' $id && docker exec $id sh -c 'cat /sys/fs/cgroup/cpu.stat; cat /sys/fs/cgroup/memory.current | sed s/^/memory_current=/; cat /sys/fs/cgroup/pids.current | sed s/^/pids_current=/'"
        args = (
            ["bash", "-lc", command]
            if host.local
            else ["ssh", "-o", "BatchMode=yes", f"{self.ssh_user}@{host.address}", command]
        )
        result = subprocess.run(args, capture_output=True, text=True, timeout=max(5, self.interval), check=True)
        lines = result.stdout.splitlines()
        raw = json.loads(lines[0])
        memory = raw.get("MemUsage", "").split("/")
        cgroup = dict(
            line.split("=", 1) if "=" in line else line.split(maxsplit=1)
            for line in lines[1:]
            if "=" in line or " " in line
        )
        rx_bytes, tx_bytes = _io_pair(raw.get("NetIO", ""))
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "host": host.id,
            "container_id": raw.get("ID"),
            "cpu_percent": float(raw.get("CPUPerc", "0").strip("%")),
            "cpu_usage_seconds": int(cgroup.get("usage_usec", 0)) / 1_000_000,
            "memory_bytes": _bytes(memory[0]) if memory else None,
            "memory_limit_bytes": _bytes(memory[1]) if len(memory) > 1 else None,
            "pids": int(cgroup.get("pids_current", raw.get("PIDs", 0))),
            "network_rx_bytes": rx_bytes,
            "network_tx_bytes": tx_bytes,
        }

    def _run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8") as handle:
            while not self.stop_event.is_set():
                sample_started = monotonic()
                with ThreadPoolExecutor(max_workers=len(self.hosts)) as pool:
                    futures = {pool.submit(self._sample, host): host for host in self.hosts}
                    for future in as_completed(futures):
                        host = futures[future]
                        try:
                            row = future.result()
                        except Exception as error:
                            row = {"timestamp": datetime.now(UTC).isoformat(), "host": host.id, "error": str(error)}
                        handle.write(json.dumps(row) + "\n")
                        handle.flush()
                self.stop_event.wait(max(0.0, self.interval - (monotonic() - sample_started)))
