from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_active_documentation_links_and_generated_references_are_current() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_documentation.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
