from pathlib import Path

import pytest

from continuum_bench.config import load_config


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def config():
    return load_config(ROOT / "configs/smoke-cumulative.toml")
