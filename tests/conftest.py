from pathlib import Path
from dataclasses import replace

import pytest

from continuum_bench.config import load_config


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def config():
    return replace(load_config(ROOT / "tests/fixtures/benchmark.toml"), root=ROOT)
