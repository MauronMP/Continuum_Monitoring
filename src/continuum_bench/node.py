"""HTTP worker used by the five-node Docker benchmark."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import gc
import json
import os
from pathlib import Path
import platform
import resource
import signal
import struct
import sys
from threading import current_thread, main_thread
from threading import RLock
from time import perf_counter_ns, process_time_ns
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Iterator

from rdflib import Graph

from .config import load_config
from .ontology import load_graph
from .partitioning import build_role_graph, privacy_violations
from .protocol import WORKER_PROTOCOL_VERSION, WORKER_SERVICE
from .queries import execute_query, execute_query_detailed, load_catalog
from .reasoners import REASONING_CONTRACT, materialize
from .specification import ONTOLOGY_VERSION
from .synthetic import (
    add_synthetic_data,
    add_synthetic_rules,
    pad_to_target_triples,
)


def _peak_rss_kib() -> int:
    """Return the process high-water RSS using one cross-platform unit."""

    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB while Darwin reports bytes.
    return value // 1024 if sys.platform == "darwin" else value


def _current_rss_kib() -> int:
    """Return the current Linux resident set, with peak RSS as fallback."""

    try:
        for line in Path("/proc/self/status").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (FileNotFoundError, PermissionError, ValueError, IndexError):
        pass
    return _peak_rss_kib()


def _process_io_bytes() -> tuple[int, int]:
    """Return process disk bytes from Linux procfs, or zeros when unavailable."""

    try:
        fields = {}
        for line in Path("/proc/self/io").read_text(
            encoding="utf-8"
        ).splitlines():
            key, value = line.split(":", 1)
            fields[key] = int(value.strip())
        return fields.get("read_bytes", 0), fields.get("write_bytes", 0)
    except (FileNotFoundError, PermissionError, ValueError):
        return 0, 0


def _total_memory_kib() -> int:
    try:
        for line in Path("/proc/meminfo").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1])
    except (FileNotFoundError, PermissionError, ValueError, IndexError):
        pass
    return 0


class WorkerPhaseTimeout(TimeoutError):
    """Raised inside a worker when its coordinator budget expires."""


@contextmanager
def _worker_timeout(seconds: float) -> Iterator[None]:
    """Interrupt CPU-bound Python reasoning while keeping the worker alive."""

    if (
        seconds <= 0
        or not hasattr(signal, "setitimer")
        or current_thread() is not main_thread()
    ):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def alarm_handler(signum, frame):  # noqa: ARG001
        raise WorkerPhaseTimeout(
            f"worker phase exceeded {seconds:.1f}s"
        )

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _with_transport_metrics(
    payload: dict[str, Any],
    request_bytes: int,
) -> tuple[dict[str, Any], bytes]:
    """Attach exact HTTP body sizes and return the encoded response body."""

    payload["request_bytes"] = request_bytes
    payload["response_bytes"] = 0
    while True:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        encoded_size = len(encoded)
        if payload["response_bytes"] == encoded_size:
            return payload, encoded
        payload["response_bytes"] = encoded_size


class NodeRuntime:
    def __init__(self, root: Path, role: str) -> None:
        self.root = root
        self.role = role
        self.config = load_config(root / "configs/benchmark.toml")
        # The full monolithic graph is loaded lazily. Sharded workers otherwise
        # paid the memory cost of a replica they never queried.
        self.base_graph: Graph | None = None
        self.catalog = {
            spec.id: spec
            for spec in load_catalog(
                self.config.resolve(self.config.query_catalog),
                self.config.root,
            )
        }
        self.graph: Graph | None = None
        self.reasoner: str | None = None
        self.users: int | None = None
        self.seed = self.config.seed
        self.rule_count = 0
        self.target_triples = 0
        self.padding_mode = "semantic"
        self.mode = "replicated"
        self.lock = RLock()

    @staticmethod
    def _copy(source: Graph) -> Graph:
        graph = Graph()
        for prefix, namespace in source.namespaces():
            graph.bind(prefix, namespace)
        for triple in source:
            graph.add(triple)
        return graph

    def _monolithic_base(self) -> Graph:
        if self.base_graph is None:
            self.base_graph = load_graph(
                self.config.resolve(path)
                for path in self.config.ontology_files
            )
        return self.base_graph

    def prepare(
        self,
        reasoner: str,
        users: int,
        seed: int,
        mode: str = "replicated",
        rule_count: int = 0,
        target_triples: int = 0,
        padding_mode: str = "semantic",
        phase_timeout_seconds: float = 0,  # coordinator-only metadata
    ) -> dict[str, Any]:
        with self.lock:
            io_read_before, io_write_before = _process_io_bytes()
            cpu_started = process_time_ns()
            started = perf_counter_ns()
            if mode == "replicated":
                source = self._copy(self._monolithic_base())
                fragments = None
                clone_ms = (perf_counter_ns() - started) / 1_000_000
                generated_at = perf_counter_ns()
                synthetic_triples = add_synthetic_data(source, users, seed)
                generation_ms = (
                    perf_counter_ns() - generated_at
                ) / 1_000_000
            elif mode == "partitioned":
                source, fragments = build_role_graph(
                    self.config,
                    self.role,
                    users,
                    seed,
                )
                clone_ms = 0.0
                generation_ms = (
                    perf_counter_ns() - started
                ) / 1_000_000
                synthetic_triples = fragments.synthetic_triples
            else:
                raise ValueError(
                    f"Unknown data mode {mode!r}; use replicated or partitioned"
                )
            violations = (
                privacy_violations(
                    source,
                    self.role,
                    fragments.sensitive_resources,
                )
                if mode == "partitioned"
                else []
            )
            if violations:
                raise ValueError(
                    f"Privacy gate rejected {len(violations)} facts on "
                    f"{self.role}: {violations[0]}"
                )
            rule_triples = add_synthetic_rules(source, rule_count)
            padding_triples = pad_to_target_triples(
                source,
                target_triples,
                mode=padding_mode,
            )
            reasoning = materialize(source, reasoner)
            self.graph = reasoning.graph
            self.reasoner = reasoner
            self.users = users
            self.seed = seed
            self.rule_count = rule_count
            self.target_triples = target_triples
            self.padding_mode = padding_mode
            self.mode = mode
            process_cpu_ms = (process_time_ns() - cpu_started) / 1_000_000
            io_read_after, io_write_after = _process_io_bytes()
            return {
                "role": self.role,
                "mode": mode,
                "reasoner": reasoner,
                "synthetic_users": users,
                "synthetic_triples": synthetic_triples,
                "synthetic_rule_count": rule_count,
                "synthetic_rule_triples": rule_triples,
                "padding_triples": padding_triples,
                "padding_mode": padding_mode,
                "clone_ms": clone_ms,
                "generation_ms": generation_ms,
                "reasoning_ms": reasoning.duration_ms,
                "input_triples": reasoning.input_triples,
                "logical_input_triples": (
                    reasoning.input_triples
                    if fragments is None
                    else (
                        fragments.substrate_triples
                        + fragments.reference_triples
                        + fragments.synthetic_triples
                    )
                ),
                "output_triples": reasoning.output_triples,
                "inferred_triples": reasoning.inferred_triples,
                "process_cpu_ms": process_cpu_ms,
                "current_rss_kib": _current_rss_kib(),
                "peak_rss_kib": _peak_rss_kib(),
                "disk_read_bytes": max(io_read_after - io_read_before, 0),
                "disk_write_bytes": max(
                    io_write_after - io_write_before, 0
                ),
                **(
                    {}
                    if fragments is None
                    else {
                        "profile": fragments.placement_profiles[self.role],
                        "local_substrate_triples": (
                            fragments.substrate_triples_by_role[self.role]
                        ),
                    }
                ),
            }

    def recover(self) -> dict[str, Any]:
        """Rebuild the last prepared application state after a logical loss."""

        with self.lock:
            if self.reasoner is None or self.users is None:
                raise RuntimeError("Node must be prepared before recovery")
            reasoner = self.reasoner
            users = self.users
            seed = self.seed
            mode = self.mode
            rule_count = self.rule_count
            target_triples = self.target_triples
            padding_mode = self.padding_mode
            self.graph = None
            gc.collect()
            started = perf_counter_ns()
            result = self.prepare(
                reasoner,
                users,
                seed,
                mode=mode,
                rule_count=rule_count,
                target_triples=target_triples,
                padding_mode=padding_mode,
            )
            result["recovery_ms"] = (
                perf_counter_ns() - started
            ) / 1_000_000
            result["recovery_scope"] = "application_state_rebuild"
            return result

    def execute(
        self,
        query_ids: list[str],
        include_result_keys: bool = False,
    ) -> dict[str, Any]:
        with self.lock:
            if self.graph is None:
                raise RuntimeError("Node must be prepared before querying")
            unknown = sorted(set(query_ids) - set(self.catalog))
            if unknown:
                raise ValueError(f"Unknown query IDs: {unknown}")
            cpu_started = process_time_ns()
            io_read_before, io_write_before = _process_io_bytes()
            started = perf_counter_ns()
            measurements = []
            for query_id in query_ids:
                if include_result_keys:
                    execution = execute_query_detailed(
                        self.graph,
                        self.catalog[query_id],
                    )
                    item = asdict(execution.measurement)
                    item["result_keys"] = list(execution.result_keys)
                    item["result_group_keys"] = list(
                        execution.group_keys
                    )
                else:
                    item = asdict(
                        execute_query(self.graph, self.catalog[query_id])
                    )
                measurements.append(item)
            wall_ms = (perf_counter_ns() - started) / 1_000_000
            process_cpu_ms = (process_time_ns() - cpu_started) / 1_000_000
            io_read_after, io_write_after = _process_io_bytes()
            return {
                "role": self.role,
                "mode": self.mode,
                "reasoner": self.reasoner,
                "synthetic_users": self.users,
                "query_count": len(measurements),
                "query_wall_ms": wall_ms,
                "query_cpu_ms": sum(
                    float(item["duration_ms"]) for item in measurements
                ),
                "process_cpu_ms": process_cpu_ms,
                "current_rss_kib": _current_rss_kib(),
                "peak_rss_kib": _peak_rss_kib(),
                "disk_read_bytes": max(io_read_after - io_read_before, 0),
                "disk_write_bytes": max(
                    io_write_after - io_write_before, 0
                ),
                "measurements": measurements,
            }


class Handler(BaseHTTPRequestHandler):
    server: "NodeServer"

    def _json(
        self,
        status: int,
        payload: dict[str, Any],
        *,
        encoded: bytes | None = None,
    ) -> None:
        data = (
            encoded
            if encoded is not None
            else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._json(404, {"error": "not found"})
            return
        runtime = self.server.runtime
        self._json(
            200,
            {
                "status": "ok",
                "service": WORKER_SERVICE,
                "protocol_version": WORKER_PROTOCOL_VERSION,
                "ontology_version": ONTOLOGY_VERSION,
                "query_count": len(runtime.catalog),
                "reasoning_contract": REASONING_CONTRACT,
                "role": runtime.role,
                "pid": os.getpid(),
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "cpu_count": os.cpu_count() or 0,
                "pointer_bits": struct.calcsize("P") * 8,
                "total_memory_kib": _total_memory_kib(),
                "reasoner": runtime.reasoner,
                "synthetic_users": runtime.users,
                "synthetic_rule_count": runtime.rule_count,
                "target_triples": runtime.target_triples,
                "padding_mode": runtime.padding_mode,
                "mode": runtime.mode,
                "base_triples": (
                    len(runtime.base_graph)
                    if runtime.base_graph is not None
                    else 0
                ),
                "base_graph_loaded": runtime.base_graph is not None,
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        request_started = perf_counter_ns()
        phase = self.path.strip("/") or "unknown"
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} reasoner={payload.get('reasoner', '-')} "
                f"users={payload.get('users', '-')} status=running",
                flush=True,
            )
            with _worker_timeout(
                float(payload.get("phase_timeout_seconds", 0))
            ):
                if self.path == "/prepare":
                    result = self.server.runtime.prepare(
                        reasoner=str(payload["reasoner"]),
                        users=int(payload.get("users", 0)),
                        seed=int(payload.get("seed", 2026)),
                        mode=str(payload.get("mode", "replicated")),
                        rule_count=int(payload.get("rule_count", 0)),
                        target_triples=int(payload.get("target_triples", 0)),
                        padding_mode=str(
                            payload.get("padding_mode", "semantic")
                        ),
                    )
                elif self.path == "/queries":
                    result = self.server.runtime.execute(
                        [str(value) for value in payload["query_ids"]],
                        include_result_keys=bool(
                            payload.get("include_result_keys", False)
                        ),
                    )
                elif self.path == "/recover":
                    result = self.server.runtime.recover()
                else:
                    self._json(404, {"error": "not found"})
                    return
            result, encoded = _with_transport_metrics(result, length)
            self._json(200, result, encoded=encoded)
            elapsed_ms = (perf_counter_ns() - request_started) / 1_000_000
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} reasoner={result.get('reasoner', '-')} "
                f"users={result.get('synthetic_users', '-')} status=done "
                f"elapsed_ms={elapsed_ms:.2f}",
                flush=True,
            )
        except (BrokenPipeError, ConnectionResetError) as error:
            # The computation may have completed after a Wi-Fi client dropped.
            # Do not trigger a second write to the already closed socket.
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} status=client-disconnected "
                f"error={type(error).__name__}",
                flush=True,
            )
        except WorkerPhaseTimeout as error:
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} status=timeout error={error}",
                flush=True,
            )
            self._json(408, {"error": str(error), "timeout": True})
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} status=failed "
                f"error={type(error).__name__}: {error}",
                flush=True,
            )
            self._json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - process boundary
            print(
                f"[node-work] role={self.server.runtime.role} "
                f"phase={phase} status=failed "
                f"error={type(error).__name__}: {error}",
                flush=True,
            )
            self._json(500, {"error": f"{type(error).__name__}: {error}"})

    def log_message(self, format: str, *args: object) -> None:
        print(
            f"[node role={self.server.runtime.role}] "
            f"{self.address_string()} {format % args}",
            flush=True,
        )


class NodeServer(HTTPServer):
    def __init__(self, address: tuple[str, int], runtime: NodeRuntime) -> None:
        super().__init__(address, Handler)
        self.runtime = runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Continuum Docker worker node")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--root",
        default=os.environ.get("CONTINUUM_ROOT", "/app"),
    )
    parser.add_argument(
        "--role",
        default=os.environ.get("CONTINUUM_ROLE", "edge"),
    )
    args = parser.parse_args(argv)
    runtime = NodeRuntime(Path(args.root).resolve(), args.role)
    server = NodeServer((args.host, args.port), runtime)
    print(
        f"[node] role={args.role} listening={args.host}:{args.port} "
        "base_graph=lazy",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
