"""GUI tests — these DRIVE the widgets offscreen and assert real file effects.

An import-only smoke test would prove nothing, so each test loads a real card,
manipulates controls, saves, and re-reads the bytes from disk.
"""

import pathlib
import shutil
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

pytest.importorskip("PySide6")

pytestmark = pytest.mark.gui  # run in an isolated process (see run_tests.py)

from PySide6.QtWidgets import QApplication  # noqa: E402

from dmw3editor.core import memcard as mc  # noqa: E402
from dmw3editor.core.save import DMW3Save, LEVEL_MAX, MONEY_MAX, TABLES  # noqa: E402
from dmw3editor.ui import theme  # noqa: E402
from dmw3editor.ui.main_window import MainWindow  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARDS = pathlib.Path(
    r"C:\Users\space\Downloads\duckstation-windows-x64-release"
    r"\Digimon World 3 saves"
)
USA_CARD = CARDS / "digimon-world-3.21060.gme"


@pytest.fixture
def card_copy(tmp_path):
    if not USA_CARD.exists():
        pytest.skip("sample card not present on this machine")
    dest = tmp_path / USA_CARD.name
    shutil.copy2(USA_CARD, dest)
    return dest


@pytest.fixture
def win(app, card_copy, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(card_copy), ""))
    )
    w = MainWindow()
    w.open_file()
    return w


def reread(path):
    card = mc.MemoryCard.load(str(path))
    return DMW3Save(card.extract_payload(card.find_dmw3_save()))


# ---- theme ---------------------------------------------------------------
def test_theme_applies_without_error(app):
    assert app.styleSheet()
    assert "QPushButton" in app.styleSheet()


# ---- loading -------------------------------------------------------------
def test_opening_a_card_populates_controls(win):
    assert win.stack.isEnabled()
    assert win.save_btn.isEnabled()
    ed = win.slot_editors[0]
    assert ed.money.value() == 9_999_951
    assert ed.party_levels[0].value() == 98
    assert TABLES.digimon[ed.party_ids[0].currentData()] == "Guilmon"
    assert "USA" in win.subtitle.text()
    assert "valid" in win.subtitle.text()
    # ROM-region selector auto-detects USA for this card
    assert win.region_combo.currentData() == "USA"
    assert win.region_combo.isEnabled()


def test_region_selector_manual_override_rerenders(win):
    """Picking EUR in the ROM-region combo re-interprets the party-ID space
    and the subtitle without rewriting the payload."""
    before = bytes(win._save._buf)
    win.region_combo.setCurrentIndex(win.region_combo.findData("EUR"))
    assert win._save.region_guess == "EUR"
    assert "manual" in win.subtitle.text()
    # party rows now resolve through EUR party space (ids 3..10)
    ed = win.slot_editors[0]
    did = ed.party_ids[0].currentData()
    pmin = 3
    idx = did - pmin
    assert 0 <= idx < 8
    assert bytes(win._save._buf) == before  # payload untouched
    # back to auto restores the detected USA region
    win.region_combo.setCurrentIndex(win.region_combo.findData("auto"))
    assert win._save.region_guess == "USA"
    assert "manual" not in win.subtitle.text()


def test_slot_party_rows_show_avatars(win):
    # every party slot editor has a non-empty avatar pixmap for its rookie
    for ed in win.slot_editors:
        for i in range(3):
            pix = ed.party_avatars[i].pixmap()
            assert pix is not None and not pix.isNull()


def test_empty_slots_are_flagged_in_sidebar(win):
    # slot 2/3 are empty on the USA card; nav labels show it
    labels = [b.text() for b in win._nav_buttons]
    assert "empty" in labels[2].lower() or "empty" in labels[1].lower()
    assert win.slot_editors[1].empty_note.isVisible() or win.slot_editors[2].empty_note.isVisible()


def test_sidebar_navigates_pages(win):
    keys = win._keys
    assert keys[0] == "slot0"
    assert "inv-items" in keys and "packs" in keys
    win._select_page("inv-weapons")
    assert win.stack.currentIndex() == keys.index("inv-weapons")
    assert win._nav_buttons[keys.index("inv-weapons")].isChecked()
    win._select_page("hex")
    assert win.stack.currentIndex() == keys.index("hex")


def test_rejects_a_non_dmw3_card(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    junk = tmp_path / "blank.mcr"
    junk.write_bytes(bytes(131072))
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(junk), ""))
    )
    seen = {}
    monkeypatch.setattr(
        QMessageBox, "critical", staticmethod(lambda *a, **k: seen.setdefault("msg", a))
    )
    w = MainWindow()
    w.open_file()
    assert "msg" in seen
    # Save-dependent pages stay disabled when no valid card is open, but the
    # appearance (Themes) page and its nav stay usable.
    assert not w.slot_editors[0].isEnabled()
    assert not w.digimon_tab.isEnabled()
    assert w.themes_tab.isEnabled()
    themes_nav = w._nav_buttons[w._keys.index("themes")]
    assert themes_nav.isEnabled()


# ---- hex editor dev-lock -------------------------------------------------
def test_hex_editor_locked_without_dev_mode(win):
    assert not win.dev_toggle.isChecked()
    win._select_page("hex")
    page = win.hex_page
    assert page.lock_note.isVisible()
    assert not page.table.isEnabled()


def test_hex_editor_unlocks_with_dev_mode(win):
    win.dev_toggle.setChecked(True)
    page = win.hex_page
    assert page.table.isEnabled()
    assert not page.lock_note.isVisible()


def test_hex_editor_byte_edit_writes_through_model(win):
    win.dev_toggle.setChecked(True)
    page = win.hex_page
    # item slot 0 lives at payload 0x03A7 -> page 0x03A7//256=3, row 7 col 8
    page._set_page(0x03A7 // 256)
    row = (0x03A7 % 256) // 16
    col = 1 + (0x03A7 % 16)
    cell = page.table.item(row, col)
    assert cell is not None
    cell.setText("2A")
    assert win._save.item_qty(0) == 42
    assert win._dirty
    out = win._save.to_bytes()
    assert out[0x03A7] == 42


def test_hex_editor_reverts_invalid_hex(win):
    win.dev_toggle.setChecked(True)
    page = win.hex_page
    page._set_page(0x03A7 // 256)
    row = (0x03A7 % 256) // 16
    col = 1 + (0x03A7 % 16)
    old = win._save.item_qty(0)
    cell = page.table.item(row, col)
    cell.setText("ZZ")
    assert win._save.item_qty(0) == old
    assert cell.text() == f"{old:02X}"


def test_hex_editor_marks_forbidden_read_only(win):
    win.dev_toggle.setChecked(True)
    page = win.hex_page
    page._set_page(0x5000 // 256)  # 0x5000 region is unverified / forbidden
    row = (0x5000 % 256) // 16
    col = 1 + (0x5000 % 16)
    item = page.table.item(row, col)
    assert item is not None
    assert not (item.flags() & ~0x1)  # not editable (ItemIsEditable not set)


# ---- editing writes real bytes ------------------------------------------
def test_editing_money_then_saving_changes_the_file(win, card_copy):
    win.slot_editors[0].money.setValue(4242)
    assert win._dirty
    win.save_file()
    assert not win._dirty
    assert reread(card_copy).slots[0].money == 4242


def test_injecting_a_digimon_persists(win, card_copy):
    # Party selectors offer only the 8 base rookies, region-correct
    # (evolved ids stall the game on load). On the USA fixture id 6 =
    # Guilmon.
    combo = win.slot_editors[0].party_ids[0]
    combo.setCurrentIndex(combo.findData(6))
    win.slot_editors[0].party_levels[0].setValue(LEVEL_MAX)
    win.save_file()

    slot = reread(card_copy).slots[0]
    assert slot.party[0] == (6, LEVEL_MAX)
    assert reread(card_copy).checksum_valid


def test_max_buttons_work(win):
    ed = win.slot_editors[0]
    ed.party_levels[0].setValue(5)
    ed._max_levels()
    assert [w.value() for w in ed.party_levels] == [LEVEL_MAX] * 3


def test_money_spinbox_is_clamped_to_game_max(win):
    ed = win.slot_editors[0]
    ed.money.setValue(99_999_999)
    assert ed.money.value() == MONEY_MAX


def test_saving_creates_a_backup(win, card_copy):
    original = card_copy.read_bytes()
    win.slot_editors[0].money.setValue(777)
    win.save_file()
    backup = card_copy.with_suffix(card_copy.suffix + ".bak")
    assert backup.exists()
    assert backup.read_bytes() == original


def test_editing_one_slot_leaves_the_others_untouched(win, card_copy):
    before = reread(card_copy)
    other_1 = before.slots[1].money
    other_2 = before.slots[2].play_time
    win.slot_editors[0].money.setValue(31337)
    win.save_file()
    after = reread(card_copy)
    assert after.slots[0].money == 31337
    assert after.slots[1].money == other_1
    assert after.slots[2].play_time == other_2


def test_save_is_surgical_across_the_whole_card(win, card_copy):
    original = card_copy.read_bytes()
    win.slot_editors[0].money.setValue(1000)
    win.save_file()
    new = card_copy.read_bytes()
    changed = [i for i in range(len(original)) if original[i] != new[i]]
    # 4 money bytes + up to 2 checksum bytes.
    assert len(changed) <= 6, [hex(c) for c in changed]
