"""Test runner for the DMW3 save editor.

WHY A CUSTOM RUNNER
-------------------
On this Windows host, Qt (PySide6) and numpy cannot coexist in the SAME pytest
process: once the numpy/MKL runtime is loaded, initializing a QApplication later
in the same process crashes it (status 0xC0000409). The crash also happens under
the offscreen backend.  The fix is process isolation:

  * core tests (no Qt)  -> one process
  * GUI tests (Qt)      -> a separate process, on the native Windows platform

Run with:  python run_tests.py
Or manually:
  pytest tests/ -m "not gui"            # safe, no display needed
  pytest tests/ -m gui                  # needs a display (native backend)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")


def _run(args: list[str], extra_env: dict[str, str] | None = None) -> int:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    env.pop("QT_QPA_PLATFORM", None)  # let GUI tests use the native backend
    print(f"\n$ pytest {' '.join(args)}\n" + "-" * 60)
    return subprocess.run([PY, "-m", "pytest", *args], cwd=ROOT, env=env).returncode


def main() -> int:
    rc = 0
    # 1) Core / non-GUI tests — safe in any environment.
    rc |= _run(["tests/", "-m", "not gui", "-q", "-p", "no:cacheprovider"])
    # 2) GUI tests — separate process, native backend (offscreen crashes here).
    #    We name the GUI test FILES explicitly (never the whole tests/ dir):
    #    collecting the full suite imports numpy-using modules too, and Qt +
    #    numpy in one process crashes on this host.
    rc |= _run(
        [
            "tests/test_gui.py",
            "tests/test_field_locator.py",
            "tests/test_collections_gui.py",
            "-m",
            "gui",
            "-o",
            "addopts=",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        extra_env={"QT_QPA_PLATFORM": "windows"},
    )
    print("\n" + "=" * 60)
    print("OVERALL:", "PASS" if rc == 0 else f"FAIL (rc={rc})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
