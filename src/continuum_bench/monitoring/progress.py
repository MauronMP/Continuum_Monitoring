"""Durable, human-readable progress for long physical experiments."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any


class PointProgress:
    """Report benchmark-point progress and persist the latest state atomically."""

    def __init__(self, output: Path, family: str, total: int) -> None:
        if total < 1:
            raise ValueError("Progress total must be positive")
        self.output = output
        self.family = family
        self.total = total
        self.completed = 0
        self.started_at = datetime.now(timezone.utc).isoformat()

    def start(self, **context: Any) -> None:
        self._emit("running", self.completed + 1, context)

    def finish(self, status: str, **context: Any) -> None:
        self.completed += 1
        self._emit(status, self.completed, context)

    def _emit(self, status: str, point: int, context: dict[str, Any]) -> None:
        percent = 100.0 * point / self.total
        fields = " ".join(
            f"{key}={value}" for key, value in context.items() if value is not None
        )
        print(
            f"[benchmark-progress] family={self.family} point={point}/{self.total} "
            f"percent={percent:.1f} status={status} {fields}".rstrip(),
            flush=True,
        )
        payload = {
            "family": self.family,
            "status": status,
            "point": point,
            "completed_points": self.completed,
            "total_points": self.total,
            "percent": percent,
            "started_at": self.started_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current": context,
        }
        self.output.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.output,
                prefix=".progress.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.output / "progress.json")
        except BaseException:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise
