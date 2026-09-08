"""Headless, writable Matplotlib setup shared by report modules."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile


def configure_matplotlib() -> None:
    config_dir = Path(tempfile.gettempdir()) / "continuum-matplotlib"
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(config_dir))
    import matplotlib

    matplotlib.use("Agg")
