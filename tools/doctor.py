"""Run read-only diagnostics without installing the package first."""

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit(
        "Se requiere Python >=3.11. En Ubuntu 22.04 seleccione un intérprete más reciente o use Ubuntu 24.04+."
    )
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from continuum_bench.environment import main

if __name__ == "__main__":
    raise SystemExit(main())
