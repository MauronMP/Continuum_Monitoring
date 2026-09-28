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
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.frameon": False,
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
        "grid.color": "#d9d9d9",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.6,
        "figure.dpi": 120,
        "savefig.dpi": 300,
    })
