"""Robust CSV output shared by benchmark and reporting commands."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import tempfile
from typing import Any


def write_dict_rows(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    empty_message: str,
) -> None:
    """Write heterogeneous dictionaries without exposing partial output files."""
    if not rows:
        raise ValueError(empty_message)

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(
        dict.fromkeys(key for row in rows for key in row)
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                restval="",
            )
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
