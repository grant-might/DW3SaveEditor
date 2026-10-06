"""Tests for the capture auto-decoder (research/scripts/run_captures.py).

These prove the harness isolates exactly the bytes a single edit changed, using
a known pair (original card vs the BOOTTEST card with the verified 6-byte edit).
This is the consumer side of the controlled-diff pipeline.
"""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "scripts" / "run_captures.py"
OUT = ROOT / "research" / "captures_report.json"
ORIG = pathlib.Path(
    r"C:\Users\space\Downloads\duckstation-windows-x64-release\Digimon World 3 saves\digimon-world-3.21060.gme"
)
BOOT = ROOT / "work" / "BOOTTEST_digimon-world-3.21060.gme"


@pytest.mark.skipif(
    not ORIG.exists() or not BOOT.exists(),
    reason="needs the sample .gme cards present",
)
def test_run_captures_isolates_known_edit(tmp_path, monkeypatch):
    # point the script's CAPTURES/OUT at tmp via env-free edit: use a temp captures dir
    cap = tmp_path / "captures"
    cap.mkdir()
    shutil.copy(ORIG, cap / "before_ITEM.gme")
    shutil.copy(BOOT, cap / "after_ITEM.gme")

    env = dict(os.environ)
    # run_captures uses hardcoded ROOT paths; invoke it with a patched module instead
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_captures", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # monkeypatch the module's path constants
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "CAPTURES", str(cap))
    out = tmp_path / "report.json"
    monkeypatch.setattr(mod, "OUT", str(out))

    code = mod.main()
    assert code == 0
    report = __import__("json").load(open(out, encoding="utf-8"))
    assert "ITEM" in report["pairs"]
    deltas = report["pairs"]["ITEM"]["deltas"]
    # the known BOOTTEST edit touches: checksum(2) + money(4) + 3 party ids(12) + 1 level(2)
    known = {d["known_as"] for d in deltas}
    assert "slot1.money (u32)" in known
    assert "slot1.party[0].id (u32)" in known
    assert "slot1.party[0].level (u16)" in known
    assert report["pairs"]["ITEM"]["changed_bytes"] == 6
