"""Smoke test for the boot-card verifier script (work/verify_boot_card.py).

The verifier is a standalone script, not importable as a module, so we exercise
it as a subprocess: it must run with exit code 0 against the shipped BOOTTEST
card and report a valid checksum. This keeps the script under the test gate.
"""
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "work" / "verify_boot_card.py"
ORIG = pathlib.Path(
    r"C:\Users\space\Downloads\duckstation-windows-x64-release\Digimon World 3 saves\digimon-world-3.21060.gme"
)
BOOT = ROOT / "work" / "BOOTTEST_digimon-world-3.21060.gme"

pytestmark = pytest.mark.gui  # runs in the isolated GUI-stage process


@pytest.mark.skipif(
    not ORIG.exists() or not BOOT.exists(),
    reason="needs the sample .gme cards present",
)
def test_verify_boot_card_runs_clean():
    r = subprocess.run(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr[-800:]
    assert "checksum valid: True" in r.stdout
    assert "VERDICT: card is structurally valid" in r.stdout
