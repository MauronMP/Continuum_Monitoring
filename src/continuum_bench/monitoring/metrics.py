"""Process measurements, independent from experiment orchestration and plots."""
import os
import time
from pathlib import Path

class ProcessMetrics:
    def snapshot(self):
        rss = None
        status = Path('/proc/self/status')
        if status.exists():
            for line in status.read_text().splitlines():
                if line.startswith('VmRSS:'):
                    rss = int(line.split()[1]) / 1024
        return {"wall_seconds": time.perf_counter(), "cpu_seconds": time.process_time(),
                "rss_mib": rss, "cpu_cores": os.cpu_count() or 1}


def measured(before, after):
    elapsed = after['wall_seconds'] - before['wall_seconds']
    cpu = after['cpu_seconds'] - before['cpu_seconds']
    return {"execution_ms": elapsed * 1000, "cpu_ms": cpu * 1000,
            "cpu_percent_one_core": 100 * cpu / elapsed if elapsed else None,
            "rss_mib": after['rss_mib']}
