"""Discover independently managed native semantic-engine services."""
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from .engines import discover

DEFAULT_ENGINE_URLS = tuple(f"http://127.0.0.1:{port}" for port in range(8291, 8295))

@contextmanager
def semantic_engine_stack(root: Path, *, keep_running: bool = False) -> Iterator[tuple[str, ...]]:
    """Use native services; lifecycle remains with their host administrator."""
    try:
        discover(DEFAULT_ENGINE_URLS)
    except Exception as error:
        raise RuntimeError(
            "Native semantic engines are unavailable. Start the native services "
            "on ports 8291–8294 or pass engines --endpoints URLS."
        ) from error
    yield DEFAULT_ENGINE_URLS
