"""Lifecycle management for the default semantic-engine Docker stack."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
from time import monotonic, sleep
from typing import Iterator

from .engines import EngineEndpoint, discover


DEFAULT_ENGINE_URLS = (
    "http://127.0.0.1:8291",
    "http://127.0.0.1:8292",
    "http://127.0.0.1:8293",
    "http://127.0.0.1:8294",
)


def _compose(root: Path, *arguments: str) -> None:
    compose_file = root / "docker-compose.engines.yml"
    environment = os.environ.copy()
    docker_desktop_bin = Path(
        "/Applications/Docker.app/Contents/Resources/bin"
    )
    if docker_desktop_bin.is_dir():
        environment["PATH"] = (
            f"{docker_desktop_bin}{os.pathsep}"
            f"{environment.get('PATH', '')}"
        )
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                *arguments,
            ],
            cwd=root,
            env=environment,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "Docker is required for the automatic Jena/RDF4J engine tests"
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Docker Compose could not manage the semantic-engine stack"
        ) from error


def _ready(
    urls: tuple[str, ...],
    timeout_seconds: float = 120.0,
) -> list[EngineEndpoint]:
    deadline = monotonic() + timeout_seconds
    last_error: Exception | None = None
    while monotonic() < deadline:
        try:
            return discover(urls)
        except Exception as error:  # Services cross a process boundary.
            last_error = error
            sleep(0.5)
    raise RuntimeError(
        "Semantic engines did not become ready within "
        f"{timeout_seconds:.0f}s: {last_error}"
    )


@contextmanager
def semantic_engine_stack(
    root: Path,
    *,
    keep_running: bool = False,
) -> Iterator[tuple[str, ...]]:
    """Ensure all default engines are available and clean up owned services."""

    urls = DEFAULT_ENGINE_URLS
    started_here = False
    try:
        discover(urls)
        print(
            "[engine-stack] status=reusing services=rdflib,jena,rdf4j,oxigraph",
            flush=True,
        )
    except Exception:
        print(
            "[engine-stack] status=starting services=rdflib,jena,rdf4j,oxigraph",
            flush=True,
        )
        _compose(root, "up", "-d", "--build")
        started_here = True
        _ready(urls)
        print("[engine-stack] status=ready", flush=True)

    try:
        yield urls
    finally:
        if started_here and not keep_running:
            print("[engine-stack] status=stopping", flush=True)
            _compose(root, "down")
