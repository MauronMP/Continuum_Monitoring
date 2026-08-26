"""Coordinator for replicated five-node Docker benchmarks."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import RemoteDisconnected
import json
from pathlib import Path
import platform
from time import perf_counter_ns, sleep
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import BenchmarkConfig
from .csv_utils import write_dict_rows
from .protocol import worker_health_error
from .queries import QuerySpec, by_categories, load_catalog


@dataclass(frozen=True)
class Endpoint:
    url: str
    role: str


CLOUD_CATEGORIES = {
    "topology",
    "semantic_schema",
    "decision",
    "consent",
    "contract_compliance",
    "policy",
}
FOG_CATEGORIES = {"migration", "delegation", "federation", "privacy"}
EDGE_CATEGORIES = {
    "observability",
    "access_control",
    "context",
    "wellbeing",
}

# Raspberry Pi reasoning/materialisation can legitimately exceed the previous
# five-minute urllib default. Retries are deliberately visible and their delay
# remains inside the measured distributed phase wall time.
DISTRIBUTED_REQUEST_TIMEOUT_SECONDS = 900.0
DISTRIBUTED_REQUEST_RETRIES = 2


def _request(
    url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 300.0,
    retries: int = 0,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_url = f"{url.rstrip('/')}{path}"
    for attempt in range(retries + 1):
        request = Request(
            request_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read())
                if isinstance(result, dict):
                    result["_coordinator_attempts"] = attempt + 1
                return result
        except HTTPError:
            # Application errors are deterministic and must not be hidden by
            # transport retries.
            raise
        except (
            ConnectionError,
            OSError,
            RemoteDisconnected,
            TimeoutError,
            URLError,
        ) as error:
            if attempt >= retries:
                raise
            delay_seconds = 0.5 * (2**attempt)
            print(
                "[distributed-http] "
                f"path={path} endpoint={url.rstrip('/')} "
                f"attempt={attempt + 1}/{retries + 1} "
                f"status=retrying delay_s={delay_seconds:.1f} "
                f"error={type(error).__name__}",
                flush=True,
            )
            sleep(delay_seconds)
    raise AssertionError("unreachable")


def discover(urls: Iterable[str]) -> list[Endpoint]:
    endpoints = []
    for url in urls:
        health = _request(url, "/health", timeout=5.0, retries=1)
        contract_error = worker_health_error(health)
        if contract_error is not None:
            raise RuntimeError(
                f"Incompatible continuum worker at {url}: {contract_error}. "
                "Stop the service occupying that port, or use a different "
                "physical-node port and redeploy."
            )
        endpoints.append(
            Endpoint(url=url.rstrip("/"), role=str(health["role"]))
        )
    roles = [endpoint.role for endpoint in endpoints]
    if roles.count("cloud") != 1 or roles.count("fog") != 1:
        raise ValueError(f"Expected one cloud and one fog, got roles={roles}")
    if sum(role.startswith("edge") for role in roles) != 3:
        raise ValueError(f"Expected three edges, got roles={roles}")
    return endpoints


def _parallel(
    endpoints: list[Endpoint],
    path: str,
    payloads: dict[str, dict[str, Any]],
    *,
    phase: str | None = None,
    timeout: float = DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
    retries: int = DISTRIBUTED_REQUEST_RETRIES,
) -> tuple[float, dict[str, dict[str, Any]]]:
    started = perf_counter_ns()
    results: dict[str, dict[str, Any]] = {}
    phase_name = phase or path.strip("/") or "request"
    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        submitted_at: dict[str, int] = {}
        futures = {
            executor.submit(
                _request,
                endpoint.url,
                path,
                payloads[endpoint.url],
                timeout,
                retries,
            ): endpoint
            for endpoint in endpoints
            if endpoint.url in payloads
        }
        for endpoint in futures.values():
            submitted_at[endpoint.url] = perf_counter_ns()
        for future in as_completed(futures):
            endpoint = futures[future]
            endpoint_ms = (
                perf_counter_ns() - submitted_at[endpoint.url]
            ) / 1_000_000
            try:
                results[endpoint.url] = future.result()
            except Exception as error:
                print(
                    "[distributed-node] "
                    f"phase={phase_name} role={endpoint.role} "
                    f"endpoint={endpoint.url} status=failed "
                    f"elapsed_ms={endpoint_ms:.2f} "
                    f"error={type(error).__name__}: {error}",
                    flush=True,
                )
                raise RuntimeError(
                    f"Distributed phase {phase_name!r} failed on "
                    f"role={endpoint.role} endpoint={endpoint.url} after "
                    f"{endpoint_ms:.2f} ms: {type(error).__name__}: {error}"
                ) from error
            print(
                "[distributed-node] "
                f"phase={phase_name} role={endpoint.role} "
                f"endpoint={endpoint.url} status=done "
                f"elapsed_ms={endpoint_ms:.2f}",
                flush=True,
            )
    wall_ms = (perf_counter_ns() - started) / 1_000_000
    return wall_ms, results


def _assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
) -> dict[str, list[QuerySpec]]:
    cloud = next(endpoint for endpoint in endpoints if endpoint.role == "cloud")
    fog = next(endpoint for endpoint in endpoints if endpoint.role == "fog")
    edges = sorted(
        (endpoint for endpoint in endpoints if endpoint.role.startswith("edge")),
        key=lambda endpoint: endpoint.role,
    )
    assigned = {endpoint.url: [] for endpoint in endpoints}
    edge_index = 0
    for spec in specs:
        if spec.category in CLOUD_CATEGORIES:
            endpoint = cloud
        elif spec.category in FOG_CATEGORIES:
            endpoint = fog
        elif spec.category in EDGE_CATEGORIES:
            endpoint = edges[edge_index % len(edges)]
            edge_index += 1
        else:
            raise ValueError(f"No Docker role assignment for {spec.category}")
        assigned[endpoint.url].append(spec)
    return assigned


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(
        path,
        rows,
        empty_message=f"Cannot write empty CSV: {path}",
    )


def _metadata(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    suite: str,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": "docker-replicated-query-routing",
        "endpoints": [
            {"url": endpoint.url, "role": endpoint.role}
            for endpoint in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "replica_count": len(endpoints),
    }


def _prepare(
    endpoints: list[Endpoint],
    reasoner: str,
    users: int,
    seed: int,
) -> tuple[float, dict[str, dict[str, Any]]]:
    payloads = {
        endpoint.url: {
            "reasoner": reasoner,
            "users": users,
            "seed": seed,
        }
        for endpoint in endpoints
    }
    return _parallel(endpoints, "/prepare", payloads, phase="prepare")


def _query(
    endpoints: list[Endpoint],
    assignment: dict[str, list[QuerySpec]],
) -> tuple[float, dict[str, dict[str, Any]]]:
    payloads = {
        url: {"query_ids": [spec.id for spec in specs]}
        for url, specs in assignment.items()
        if specs
    }
    return _parallel(endpoints, "/queries", payloads, phase="queries")


def _detail_rows(
    responses: dict[str, dict[str, Any]],
    endpoint_by_url: dict[str, Endpoint],
    common: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for url, response in responses.items():
        endpoint = endpoint_by_url[url]
        for measurement in response["measurements"]:
            rows.append(
                {
                    **common,
                    "endpoint": url,
                    "role": endpoint.role,
                    **measurement,
                }
            )
    return rows


def run_docker_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
) -> Path:
    endpoints = discover(endpoint_urls)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for reasoner in config.reasoners:
        for repetition in range(1, config.repetitions + 1):
            print(
                f"[docker-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                "nodes=5 phase=prepare status=running",
                flush=True,
            )
            prepare_wall_ms, prepared = _prepare(
                endpoints, reasoner, 0, config.seed
            )
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active.add(category)
                active_specs = by_categories(specs, active)
                assignment = _assignment(active_specs, endpoints)
                print(
                    f"[docker-cumulative] reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    "status=running",
                    flush=True,
                )
                query_wall_ms, responses = _query(endpoints, assignment)
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                }
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                node_query_ms = sum(
                    float(response["query_cpu_ms"])
                    for response in responses.values()
                )
                summary = {
                    **common,
                    "query_count": len(active_specs),
                    "prepare_wall_ms": prepare_wall_ms,
                    "node_reasoning_ms_sum": sum(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "max_node_reasoning_ms": max(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "query_wall_ms": query_wall_ms,
                    "node_query_ms_sum": node_query_ms,
                    "total_wall_ms": prepare_wall_ms + query_wall_ms,
                    "input_triples_per_replica": next(
                        iter(prepared.values())
                    )["input_triples"],
                    "output_triples_per_replica": next(
                        iter(prepared.values())
                    )["output_triples"],
                }
                summaries.append(summary)
                print(
                    f"[docker-cumulative] reasoner={reasoner} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(config, endpoints, "cumulative")
    metadata["category_order"] = list(config.category_order)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_docker_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
) -> Path:
    endpoints = discover(endpoint_urls)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    assignment = _assignment(specs, endpoints)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            for repetition in range(1, config.repetitions + 1):
                print(
                    f"[docker-scalability] block={block}/{len(config.scale_users)} "
                    f"users={users} reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    "nodes=5 phase=prepare status=running",
                    flush=True,
                )
                prepare_wall_ms, prepared = _prepare(
                    endpoints, reasoner, users, config.seed
                )
                query_wall_ms, responses = _query(endpoints, assignment)
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": next(
                        iter(prepared.values())
                    )["synthetic_triples"],
                }
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                summary = {
                    **common,
                    "query_count": len(specs),
                    "prepare_wall_ms": prepare_wall_ms,
                    "node_generation_ms_sum": sum(
                        float(item["generation_ms"])
                        for item in prepared.values()
                    ),
                    "node_reasoning_ms_sum": sum(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "max_node_reasoning_ms": max(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "query_wall_ms": query_wall_ms,
                    "node_query_ms_sum": sum(
                        float(response["query_cpu_ms"])
                        for response in responses.values()
                    ),
                    "total_wall_ms": prepare_wall_ms + query_wall_ms,
                    "input_triples_per_replica": next(
                        iter(prepared.values())
                    )["input_triples"],
                    "output_triples_per_replica": next(
                        iter(prepared.values())
                    )["output_triples"],
                }
                summaries.append(summary)
                print(
                    f"[docker-scalability] block={block}/{len(config.scale_users)} "
                    f"users={users} reasoner={reasoner} status=done "
                    f"queries={len(specs)} wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(config, endpoints, "scalability")
    metadata["scale_users"] = list(config.scale_users)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
