"""Dedicated entry points for the two smoke benchmark suites."""

from __future__ import annotations

from pathlib import Path

from .cli import main


def _project_root() -> Path:
    working_tree = Path.cwd()
    if (working_tree / "configs").is_dir():
        return working_tree
    editable_tree = Path(__file__).resolve().parents[2]
    if (editable_tree / "configs").is_dir():
        return editable_tree
    raise FileNotFoundError(
        "Run the smoke command from the project root containing configs/"
    )


def main_cumulative() -> int:
    root = _project_root()
    return main(
        [
            "--config",
            str(root / "configs/smoke-cumulative.toml"),
            "benchmark",
            "cumulative",
        ]
    )


def main_scalability() -> int:
    root = _project_root()
    return main(
        [
            "--config",
            str(root / "configs/smoke-scalability.toml"),
            "benchmark",
            "scalability",
        ]
    )
