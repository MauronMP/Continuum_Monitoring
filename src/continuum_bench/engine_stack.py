"""Lifecycle management for the default semantic-engine Docker stack."""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, sleep
from typing import Iterator

from .engines import EngineEndpoint, discover
from .environment import (
    docker_checks,
    docker_environment,
    project_checks,
    require_checks,
    runtime_checks,
)
from .processes import run_logged

DEFAULT_ENGINE_URLS = (
    "http://127.0.0.1:8291",
    "http://127.0.0.1:8292",
    "http://127.0.0.1:8293",
    "http://127.0.0.1:8294",
)


def _compose(root: Path, *arguments: str) -> None:
    timeout = float(os.environ.get("CONTINUUM_COMPOSE_TIMEOUT", "1200"))
    run_logged(
        [
            "docker",
            "compose",
            "-f",
            str(root / "docker-compose.engines.yml"),
            *arguments,
        ],
        root=root,
        environment=docker_environment(),
        timeout=timeout if arguments and arguments[0] in {"build", "up"} else 60,
        label="compose",
    )


def preflight(root: Path) -> None:
    """Fail before spending time on Python benchmarks when Docker is unusable."""
    checks = runtime_checks() + project_checks(root) + docker_checks(root)
    for check in checks:
        if check.status == "warning":
            print(f"[engine-stack] warning={check.detail} {check.hint}", flush=True)
    require_checks(checks)


def prepare_images(root: Path, *, checked: bool = False) -> None:
    if not checked:
        preflight(root)
    # Each pair shares an image. Building representatives once avoids parallel
    # exports to the same tag and reduces load on small Ubuntu hosts.
    _compose(root, "build", "rdflib")
    _compose(root, "build", "jena")


def _diagnose_startup(root: Path) -> None:
    for arguments in (("ps", "-a"), ("logs", "--no-color", "--tail", "60")):
        try:
            _compose(root, *arguments)
        except Exception as error:
            print(
                f"[engine-stack] diagnostics_error={error}", file=sys.stderr, flush=True
            )


def _ready(
    urls: tuple[str, ...],
    timeout_seconds: float = 120.0,
) -> list[EngineEndpoint]:
    deadline = monotonic() + timeout_seconds
    last_error: Exception | None = None
    while monotonic() < deadline:
        try:
            return discover(urls, timeout=2.0)
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
        preflight(root)
        try:
            prepare_images(root, checked=True)
            _compose(root, "up", "-d", "--no-build")
            started_here = True
            _ready(urls)
        except Exception as error:
            _diagnose_startup(root)
            error.add_note(
                "Se conservan los servicios para diagnóstico. Los logs están en "
                "outputs/runtime/setup/. No se han eliminado imágenes ni volúmenes. "
                "Tras revisar, puede detener este stack con "
                "'docker compose -f docker-compose.engines.yml down'."
            )
            raise
        print("[engine-stack] status=ready", flush=True)

    primary_error: BaseException | None = None
    try:
        yield urls
    except BaseException as error:
        primary_error = error
        raise
    finally:
        if started_here and not keep_running:
            print("[engine-stack] status=stopping", flush=True)
            try:
                _compose(root, "down")
            except Exception as error:
                if primary_error is None:
                    error.add_note(
                        "Las pruebas finalizaron; el fallo ocurrió al retirar los servicios Docker."
                    )
                    raise
                primary_error.add_note(f"Además falló el cierre de Compose: {error}")
                print(
                    f"[engine-stack] cleanup_error={error}", file=sys.stderr, flush=True
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare independent semantic-engine images without starting benchmarks."
    )
    parser.add_argument("action", choices=("prepare",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    prepare_images(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
