"""HTTP worker for RDFLib-RDFS and Oxigraph cross-engine benchmarks."""

from __future__ import annotations

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import os
from threading import RLock
from time import perf_counter_ns
from typing import Any

import pyoxigraph
from pyoxigraph import QueryBoolean, RdfFormat, Store
import rdflib
from rdflib import Graph
import owlrl

from .queries import QueryMeasurement
from .reasoners import REASONING_CONTRACT, materialize
from .engine_protocol import ENGINE_PROTOCOL_VERSION, ENGINE_SERVICE


class ExternalRuntime:
    def __init__(self, engine: str) -> None:
        if engine not in {"rdflib", "oxigraph"}:
            raise ValueError("Python external engine must be rdflib or oxigraph")
        self.engine = engine
        self.version = (
            f"rdflib={rdflib.__version__};owlrl={owlrl.__version__}"
            if engine == "rdflib"
            else pyoxigraph.__version__
        )
        self.inference_profile = "rdfs" if engine == "rdflib" else "none"
        self.graph: Graph | None = None
        self.store: Store | None = None
        self.lock = RLock()

    def prepare(self, data: str) -> dict[str, Any]:
        payload = data.encode("utf-8")
        with self.lock:
            started = perf_counter_ns()
            if self.engine == "rdflib":
                source = Graph()
                source.parse(data=payload, format="nt")
                load_ms = (perf_counter_ns() - started) / 1_000_000
                reasoning = materialize(source, "rdfs")
                self.graph = reasoning.graph
                self.store = None
                input_triples = reasoning.input_triples
                output_triples = reasoning.output_triples
                reasoning_ms = reasoning.duration_ms
            else:
                store = Store()
                store.load(payload, format=RdfFormat.N_TRIPLES)
                load_ms = (perf_counter_ns() - started) / 1_000_000
                self.store = store
                self.graph = None
                input_triples = len(store)
                output_triples = input_triples
                reasoning_ms = 0.0
            prepare_ms = (perf_counter_ns() - started) / 1_000_000
            return {
                "engine": self.engine,
                "inference_profile": self.inference_profile,
                "input_triples": input_triples,
                "output_triples": output_triples,
                "inferred_triples": output_triples - input_triples,
                "load_ms": load_ms,
                "reasoning_ms": reasoning_ms,
                "prepare_ms": prepare_ms,
            }

    def execute(self, queries: list[dict[str, str]]) -> dict[str, Any]:
        with self.lock:
            if self.graph is None and self.store is None:
                raise RuntimeError("Engine must be prepared before querying")
            started = perf_counter_ns()
            measurements = [self._execute_one(query) for query in queries]
            return {
                "engine": self.engine,
                "inference_profile": self.inference_profile,
                "query_wall_ms": (perf_counter_ns() - started) / 1_000_000,
                "measurements": [asdict(item) for item in measurements],
            }

    def _execute_one(self, query: dict[str, str]) -> QueryMeasurement:
        started = perf_counter_ns()
        ask_result: bool | None
        if self.graph is not None:
            result = self.graph.query(query["text"])
            if result.type == "ASK":
                ask_result = bool(result.askAnswer)
                result_count = int(ask_result)
            else:
                ask_result = None
                result_count = sum(1 for _ in result)
        else:
            assert self.store is not None
            result = self.store.query(query["text"])
            if isinstance(result, QueryBoolean):
                ask_result = bool(result)
                result_count = int(ask_result)
            else:
                ask_result = None
                result_count = sum(1 for _ in result)
        return QueryMeasurement(
            query_id=query["id"],
            category=query["category"],
            tier=query["tier"],
            duration_ms=(perf_counter_ns() - started) / 1_000_000,
            result_count=result_count,
            ask_result=ask_result,
        )


class Handler(BaseHTTPRequestHandler):
    server: "ExternalServer"

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
                "service": ENGINE_SERVICE,
                "protocol_version": ENGINE_PROTOCOL_VERSION,
                "engine": runtime.engine,
                "version": runtime.version,
                "inference_profile": runtime.inference_profile,
                "reasoning_contract": REASONING_CONTRACT,
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/prepare":
                response = self.server.runtime.prepare(
                    str(payload["data_ntriples"])
                )
            elif self.path == "/queries":
                response = self.server.runtime.execute(payload["queries"])
            else:
                self._json(404, {"error": "not found"})
                return
            self._json(200, response)
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            self._json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - process boundary
            self._json(500, {"error": f"{type(error).__name__}: {error}"})

    def log_message(self, format: str, *args: object) -> None:
        print(
            f"[external-node engine={self.server.runtime.engine}] "
            f"{format % args}",
            flush=True,
        )


class ExternalServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        runtime: ExternalRuntime,
    ) -> None:
        super().__init__(address, Handler)
        self.runtime = runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--engine",
        default=os.environ.get("CONTINUUM_ENGINE", "rdflib"),
    )
    args = parser.parse_args(argv)
    runtime = ExternalRuntime(args.engine)
    server = ExternalServer((args.host, args.port), runtime)
    print(
        f"[external-node] engine={runtime.engine} "
        f"inference={runtime.inference_profile} "
        f"listening={args.host}:{args.port}",
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
