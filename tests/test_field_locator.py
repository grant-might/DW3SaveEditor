"""Field Locator + diff CLI tests.

These prove the controlled-diff path works end to end through the UI and the
command line. The Field Locator must isolate exactly the bytes a single action
changed, and must not write anything.
"""

import pathlib
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

pytestmark = pytest.mark.gui  # run in an isolated process (see run_tests.py)

from dmw3editor.core import memcard as mc
from dmw3editor.core.save import DMW3Save
from dmw3editor.ui.field_locator import FieldLocator

# The old Downloads path no longer exists (saves were moved / cleaned up).
# The same USA card lives in the project samples, which is what the rest of
# the suite uses — so source the fixture from there instead.
SRC = pathlib.Path(__file__).resolve().parents[1] / "samples" / "USA_dexdrive.gme"


def _make_changed(tmp_path: pathlib.Path, new_money: int) -> pathlib.Path:
    dst = tmp_path / "changed.gme"
    shutil.copy2(SRC, dst)
    card = mc.MemoryCard.load(str(dst))
    loc = card.find_dmw3_save()
    save = DMW3Save(card.extract_payload(loc))
    save.set_money(0, new_money)
    card.reinsert_payload(save.to_bytes(), loc)
    card.save(str(dst))
    return dst


def test_field_locator_isolates_single_action(tmp_path):
    before = tmp_path / "before.gme"
    shutil.copy2(SRC, before)
    after = _make_changed(tmp_path, 55555)

    w = FieldLocator()
    w._before = str(before)
    w._after = str(after)
    w._run()

    text = w.out.toPlainText()
    assert "slot1.money (u32)" in text
    assert "payload.checksum (u8)" in text
    # The unchanged save must not have been modified by the locator.
    assert before.read_bytes() == SRC.read_bytes()


def test_field_locator_does_not_write(tmp_path):
    before = tmp_path / "before.gme"
    after = tmp_path / "after.gme"
    shutil.copy2(SRC, before)
    shutil.copy2(SRC, after)
    w = FieldLocator()
    w._before = str(before)
    w._after = str(after)
    w._run()
    # no changes at all -> "no changes"; and neither file was touched
    assert before.read_bytes() == SRC.read_bytes()
    assert after.read_bytes() == SRC.read_bytes()


def test_diff_cli(tmp_path):
    before = tmp_path / "before.gme"
    shutil.copy2(SRC, before)
    after = _make_changed(tmp_path, 1234567)
    cli = pathlib.Path(__file__).resolve().parents[1] / "dmw3editor" / "core" / "diff.py"
    res = subprocess.run(
        [sys.executable, str(cli), str(before), str(after)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, res.stderr
    assert "slot1.money (u32)" in res.stdout
    assert "payload.checksum (u8)" in res.stdout
