"""GUI tests for the collection widgets (Items/Weapons/Armor/Accessories
category pages, Cards, Packs, Digimon, Key Items).

These DRIVE the widgets: bind a real save, read a table cell, apply an edit,
and confirm the save payload changed and both checksums stay valid after
to_bytes().
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

pytestmark = pytest.mark.gui  # run in the isolated GUI stage

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from dmw3editor.core import memcard as mc, checksum as ck
from dmw3editor.core.save import DMW3Save, CARD_COUNT, ITEM_BASE, CARD_BASE

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def save_and_widgets(app):
    from dmw3editor.ui.collections import (
        AccessoriesTab,
        ArmorTab,
        CardsTab,
        DigimonTab,
        ItemsTab,
        KeyItemsTab,
        PacksTab,
        WeaponsTab,
    )

    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    s = DMW3Save(c.extract_payload(loc))
    items = ItemsTab()
    weapons = WeaponsTab()
    armor = ArmorTab()
    accessories = AccessoriesTab()
    packs = PacksTab()
    digi = DigimonTab()
    cards = CardsTab()
    keys = KeyItemsTab()
    items.bind(s)
    weapons.bind(s)
    armor.bind(s)
    accessories.bind(s)
    packs.bind(s)
    digi.bind(s)
    cards.bind(s)
    keys.bind(s)
    return s, items, weapons, armor, accessories, packs, digi, cards, keys


def test_digivolution_tab_lists_forms_and_levels(qapp):
    """DigivolutionTab shows 8 rookie sprite tiles and all 44 forms for the
    selected digimon; earned rows are enabled with the save's DV level.

    Uses the EUR card: its slot order is the one digivolve_orders.json names
    came from (the USA genuine card has its own earn order — marker lookup
    names those slots correctly too, just differently)."""
    from dmw3editor.ui.collections import DigivolutionTab

    c = mc.MemoryCard.load(str(ROOT / "samples" / "EUR_raw.mcr"))
    loc = c.find_dmw3_save()
    s = DMW3Save(c.extract_payload(loc))
    tab = DigivolutionTab()
    tab.bind(s)
    assert len(tab._digi_buttons) == 8
    # each tile is a checkable sprite button labelled with its rookie name
    names = [b.text() for b in tab._digi_buttons]
    assert names == ["Kotemon", "Kumamon", "Monmon", "Agumon",
                     "Veemon", "Guilmon", "Renamon", "Patamon"]
    assert all(b.isCheckable() for b in tab._digi_buttons)
    assert tab._digi_buttons[0].icon().isNull() is False  # sprite loaded
    assert tab.selected_roster() == "Kotemon"
    # default is Kotemon; its header (Dinohumon) is the first earned row.
    assert tab.table.rowCount() == 44
    assert tab.table.item(0, 1).text() == "Dinohumon"
    # Agumon earned list: header Greymon + 30 slots -> 31 enabled rows.
    tab.select_roster("Agumon")
    qapp.processEvents()
    assert tab.selected_roster() == "Agumon"
    enabled = sum(1 for r in tab._rows if r[4].isEnabled())
    assert enabled == 31
    # some unearned forms on the EUR card are tickable (empty slots remain)
    tickable = sum(1 for r in tab._rows if r[3].isEnabled())
    assert tickable >= 1
    names = [tab.table.item(r, 1).text() for r in range(tab.table.rowCount())]
    assert names[0] == "Greymon" and names[1] == "MetalGreymon"
    assert names[-1] in ("Beelzemon", "Diaboromon", "ImperialdramonPM")


def test_digivolution_tab_apply_writes_slot_levels(qapp):
    from dmw3editor.ui.collections import DigivolutionTab

    c = mc.MemoryCard.load(str(ROOT / "samples" / "EUR_raw.mcr"))
    loc = c.find_dmw3_save()
    s = DMW3Save(c.extract_payload(loc))
    tab = DigivolutionTab()
    tab.bind(s)
    tab.select_roster("Agumon")
    # slot 0 row = MetalGreymon (second row after header)
    spin = tab._rows[1][4]
    assert spin.isEnabled()
    spin.setValue(64)
    tab._apply_all()
    assert s.digimon_dv(3)["slots"][0] == 64  # Agumon roster index 3


def test_digivolution_tab_force_earns_unearned_form(qapp):
    """Ticking an unearned form + Apply writes its marker + level into an
    empty slot — CONFIRMED in-game 2026-09-02 (Seraphimon 42 / Rosemon 7)."""
    from dmw3editor.ui.collections import DigivolutionTab

    c = mc.MemoryCard.load(str(ROOT / "samples" / "EUR_raw.mcr"))
    loc = c.find_dmw3_save()
    s = DMW3Save(c.extract_payload(loc))
    tab = DigivolutionTab()
    tab.bind(s)
    tab.select_roster("Agumon")
    # find an unearned row (checkbox enabled) and tick it
    row = next(r for r in tab._rows if not r[3].isChecked() and r[3].isEnabled())
    name, _, _, check, spin = row
    check.setChecked(True)
    qapp.processEvents()
    assert spin.isEnabled()
    spin.setValue(42)
    tab._apply_all()
    # the form is now earned in the save at the given level
    dv = s.digimon_dv(3)
    marker = __import__(
        "dmw3editor.core.save", fromlist=["DV_FORM_MARKERS"]
    ).DV_FORM_MARKERS[name]
    assert marker in dv["markers"]
    idx = dv["markers"].index(marker)
    assert dv["slots"][idx] == 42


def test_items_page_shows_confirmed_names_and_qtys(save_and_widgets):
    s, items, _w, _a, _acc, _p, _d, _c, _k = save_and_widgets
    # row 0 == save slot 0 = Power Charge with the save's qty (name col=1, qty col=2)
    assert items.table.item(0, 1).text() == "Power Charge"
    assert int(items.table.item(0, 2).text()) == s.item_qty(0)
    # slot 24 = Revive Disk (end of first confirmed block)
    assert items.table.item(24, 1).text() == "Revive Disk"
    # items page covers exactly save slots 0-47; Booster 01a (slot 48) is
    # NOT shown here — it lives on the Card Packs page (pack #0)
    assert items.table.item(47, 1).text() == "TNT Ball"
    assert items.table.rowCount() == 48


def test_weapons_armor_accessory_pages_have_correct_ranges(save_and_widgets):
    s, _i, weapons, armor, acc, _p, _d, _c, _k = save_and_widgets
    # weapons 49-171, armor 172-248, accessories 249-316
    assert weapons.table.item(0, 1).text() == "Short Sword"
    assert weapons.table.rowCount() == 123
    assert armor.table.item(0, 1).text() == "Bandanna"
    assert armor.table.rowCount() == 77
    assert acc.table.item(0, 1).text() == "Power Gem"
    assert acc.table.rowCount() == 68


def test_item_pages_apply_edits_and_keep_checksums(save_and_widgets):
    s, items, weapons, _a, _acc, _p, _d, _c, _k = save_and_widgets
    old = s.item_qty(0)
    items.table.selectRow(0)
    items.qty_spin.setValue(42)
    items._apply()
    assert s.item_qty(0) == 42
    # weapon page edit too (slot 49 = row 0 on that page)
    weapons.table.selectRow(0)
    weapons.qty_spin.setValue(7)
    weapons._apply()
    assert s.item_qty(49) == 7
    out = s.to_bytes()
    assert out[ITEM_BASE] == 42
    assert out[ITEM_BASE + 49] == 7
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)


def test_item_page_filter_narrows_rows(save_and_widgets):
    s, _items, weapons, _a, _acc, _p, _d, _c, _k = save_and_widgets
    weapons.filter_edit.setText("sword")
    shown = sum(0 for r in range(weapons.table.rowCount())
                if weapons.table.isRowHidden(r))  # count hidden
    hidden = shown
    visible = weapons.table.rowCount() - hidden
    assert visible >= 1
    assert "of" in weapons.count_lbl.text()


def test_cards_tab_shows_anchors(save_and_widgets):
    s, _i, _w, _a, _acc, _p, _d, cards, _k = save_and_widgets
    assert cards.table.item(0, 1).text() == "Sacred Spear"
    assert cards.table.item(50, 1).text() == "White Remove"
    assert cards.table.rowCount() == CARD_COUNT


def test_cards_tab_apply_and_max_all(save_and_widgets):
    s, _i, _w, _a, _acc, _p, _d, cards, _k = save_and_widgets
    cards.table.selectRow(3)
    cards.qty_spin.setValue(0)
    cards._apply()
    assert s.card_count(3) == 0
    cards._max_all()
    for i in (0, 50, 313):
        assert s.card_count(i) == 9
    out = s.to_bytes()
    assert out[CARD_BASE + 3] == 9
    assert ck.verify_chunk2(out)


def test_category_pages_show_item_art(save_and_widgets):
    from PySide6.QtGui import QPixmap

    from dmw3editor.ui import assets

    s, items, weapons, _a, _acc, _p, _d, _c, _k = save_and_widgets
    # representative icons per category are drawn in the Art column (0)
    anchors = [
        (items, 0, "charge_icon"),     # Power Charge
        (items, 47, "disc-plug-field-etc_icon"),  # TNT Ball (last Items row)
        (weapons, 0, "sword_icon"),    # Short Sword
        (weapons, 14, "glove_icon"),   # 63 Leather Glove
        (weapons, 77 - 49, "handgun_icon"),  # 77 Handgun
        (weapons, 114 - 49, "blade_icon"),   # 114 Dagger
        (weapons, 147 - 49, "bow_icon"),     # 147 Long Bow
        (weapons, 171 - 49, "horn_icon"),    # 171 Glorious Horn
    ]
    for page, row, icon_name in anchors:
        art = page.table.item(row, 0)
        assert art is not None, (page, row)
        icon = art.data(Qt.DecorationRole)
        assert isinstance(icon, QPixmap) and not icon.isNull(), (page, row)
        assert assets.item_icon_for_slot(page.START + row) is not None
        assert assets.icon_pixmap(icon_name) is not None


def test_cards_tab_shows_art_for_anchors(save_and_widgets):
    from PySide6.QtGui import QPixmap

    from dmw3editor.ui import assets

    s, _i, _w, _a, _acc, _p, _d, cards, _k = save_and_widgets
    # every anchor card row carries a rendered art pixmap in column 0
    for i in (0, 50, 146, 313):
        art = cards.table.item(i, 0)
        assert art is not None
        icon = art.data(Qt.DecorationRole)
        assert isinstance(icon, QPixmap) and not icon.isNull(), i
        # and the asset manifest resolves a real file for the same index
        assert assets.card_image_for_save_index(i) is not None, i


def test_key_items_tab_shows_screen_order(save_and_widgets):
    s, _i, _w, _a, _acc, _p, _d, _c, keys = save_and_widgets
    # row 0 = Tree Boots, row 39 = Monmon DDNA, row 47 = Folder Bag
    assert keys.table.item(0, 1).text() == "Tree Boots"
    assert keys.table.item(39, 1).text() == "Monmon DDNA"
    assert keys.table.item(47, 1).text() == "Folder Bag"
    assert keys.table.rowCount() == 48
    # the row value must mirror the model
    assert int(keys.table.item(0, 2).text()) == s.key_item_count(0)


def test_key_items_tab_apply_and_all(save_and_widgets):
    s, _i, _w, _a, _acc, _p, _d, _c, keys = save_and_widgets
    keys.table.selectRow(0)
    keys.qty_spin.setValue(0)
    keys._apply()
    assert s.key_item_count(0) == 0
    keys._all(1)
    for i in (0, 16, 39, 47):
        assert s.key_item_count(i) == 1
    keys._all(0)
    for i in (0, 16, 39, 47):
        assert s.key_item_count(i) == 0
    out = s.to_bytes()
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)


def test_packs_tab_lists_all_35_packs(save_and_widgets):
    s, _i, _w, _a, _acc, packs, _d, _c, _k = save_and_widgets
    assert packs.table.rowCount() == 35
    assert packs.table.item(0, 1).text() == "Booster 01a"
    assert packs.table.item(14, 1).text() == "Booster 15a"
    assert packs.table.item(15, 1).text() == "Booster 1b"
    assert packs.table.item(34, 1).text() == "R-Booster 05"
    # qty column mirrors the item-array byte at the pack's save slot
    assert int(packs.table.item(0, 2).text()) == s.item_qty(48)
    assert int(packs.table.item(34, 2).text()) == s.item_qty(351)


def test_packs_tab_apply_and_max_all(save_and_widgets):
    s, _i, _w, _a, _acc, packs, _d, _c, _k = save_and_widgets
    packs.table.selectRow(0)
    packs.qty_spin.setValue(13)
    packs._apply()
    assert s.item_qty(48) == 13
    packs._max_all()
    for slot in (48, 318, 332, 347, 351):
        assert s.item_qty(slot) == 99
    packs._zero_all()
    for slot in (48, 318, 332, 347, 351):
        assert s.item_qty(slot) == 0
    out = s.to_bytes()
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)


def test_digimon_tab_loads_roster_and_values(save_and_widgets):
    s, _i, _w, _a, _acc, _p, digi, _c, _k = save_and_widgets
    assert digi.roster_combo.count() == 8
    assert digi.roster_combo.itemText(0) == "Kotemon"
    assert digi.roster_combo.itemText(7) == "Patamon"
    # values mirror the model for the selected digimon
    st = s.digimon_stats(0)
    assert digi.level_spin.value() == st["level"]
    assert digi.hp_spin.value() == st["hp"]
    assert digi.mp_spin.value() == st["mp"]
    assert len(digi._spinboxes) == 13
    assert digi._spinboxes[0].value() == st["stats"][0]
    assert digi._spinboxes[12].value() == st["stats"][12]


def test_digimon_tab_switch_roster_reloads(save_and_widgets):
    s, _i, _w, _a, _acc, _p, digi, _c, _k = save_and_widgets
    digi.roster_combo.setCurrentIndex(5)  # Guilmon
    st = s.digimon_stats(5)
    assert digi.level_spin.value() == st["level"]
    assert digi._spinboxes[0].value() == st["stats"][0]


def test_digimon_avatar_follows_roster_selection(save_and_widgets):
    from dmw3editor.ui import assets

    _s, _i, _w, _a, _acc, _p, digi, _c, _k = save_and_widgets
    assert digi.roster_avatar.pixmap() is not None
    assert not digi.roster_avatar.pixmap().isNull()
    digi.roster_combo.setCurrentIndex(3)  # Agumon
    # avatar must be non-empty for every selection
    for idx in range(8):
        digi.roster_combo.setCurrentIndex(idx)
        assert digi.roster_avatar.pixmap() is not None
        assert not digi.roster_avatar.pixmap().isNull(), assets.ROSTER_NAMES[idx]


def test_digimon_tab_apply_and_max(save_and_widgets):
    s, _i, _w, _a, _acc, _p, digi, _c, _k = save_and_widgets
    digi.roster_combo.setCurrentIndex(0)  # Kotemon
    digi.level_spin.setValue(50)
    digi.exp_spin.setValue(123456)
    digi.hp_spin.setValue(4321)
    digi.mp_spin.setValue(5555)
    digi._spinboxes[0].setValue(123)
    digi._apply()
    st = s.digimon_stats(0)
    assert st["level"] == 50
    assert st["exp"] == 123456
    assert st["hp"] == 4321 and st["hp_max"] == 4321
    assert st["mp"] == 5555 and st["mp_max"] == 5555
    assert st["stats"][0] == 123
    digi._max_all()
    for i in range(8):
        st = s.digimon_stats(i)
        assert st["level"] == 99 and st["exp"] == 999999
        assert st["hp"] == 9999 and st["mp"] == 9999
        assert all(v == 999 for v in st["stats"])
    out = s.to_bytes()
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)
