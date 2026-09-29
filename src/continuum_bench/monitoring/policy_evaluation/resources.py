"""Lightweight process sampling used by policy evaluation runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
import os
import time


def _rss_mib() -> float:
    status = Path("/proc/self/status")
    if not status.is_file():
        return 0.0
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return float(line.split()[1]) / 1024.0
    return 0.0


@dataclass(frozen=True)
class ResourceMeasurement:
    total_processing_ms: float
    process_cpu_time_ms: float
    cpu_mean_percent: float
    cpu_max_percent: float
    ram_mean_mib: float
    ram_max_mib: float


class ResourceSampler:
    def __init__(self, interval_seconds: float = 0.005):
        self.interval_seconds = interval_seconds
        self._stop = Event()
        self._samples: list[tuple[float, float, float]] = []
        self._thread: Thread | None = None

    def __enter__(self) -> "ResourceSampler":
        self._samples = [(time.perf_counter(), time.process_time(), _rss_mib())]
        self._thread = Thread(target=self._sample, name="policy-resource-sampler", daemon=True)
        self._thread.start()
        return self

    def _sample(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self._samples.append((time.perf_counter(), time.process_time(), _rss_mib()))

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        self._samples.append((time.perf_counter(), time.process_time(), _rss_mib()))

    def measurement(self) -> ResourceMeasurement:
        elapsed = max(self._samples[-1][0] - self._samples[0][0], 1e-12)
        cpu = max(self._samples[-1][1] - self._samples[0][1], 0.0)
        interval_cpu: list[float] = []
        for previous, current in zip(self._samples, self._samples[1:]):
            wall_delta = current[0] - previous[0]
            if wall_delta > 0:
                interval_cpu.append(100.0 * max(current[1] - previous[1], 0.0) / wall_delta)
        rss = [sample[2] for sample in self._samples]
        return ResourceMeasurement(
            total_processing_ms=elapsed * 1000.0,
            process_cpu_time_ms=cpu * 1000.0,
            cpu_mean_percent=100.0 * cpu / elapsed,
            cpu_max_percent=max(interval_cpu, default=100.0 * cpu / elapsed),
            ram_mean_mib=sum(rss) / len(rss),
            ram_max_mib=max(rss),
        )
