"""Run read-only diagnostics without installing the package first."""

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit(
        "Python >=3.11 is required. On Ubuntu 22.04, select a newer "
        "interpreter or use Ubuntu 24.04+."
    )
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from continuum_bench.environment import main

if __name__ == "__main__":
    raise SystemExit(main())
