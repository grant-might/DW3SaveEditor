"""Card collection tests.

The card collection is 314 byte-per-card counts (0-9) at payload 0x06A3.
CONFIRMED 2026-09-02 by two live anchors (idx0 = Sacred Spear, idx50 = White
Remove) and by the exact-314-nines run on the user's maxed card.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import memcard as mc, checksum as ck
from dmw3editor.core.save import DMW3Save, SaveError, TABLES, CARD_BASE, CARD_COUNT

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def usa_save():
    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    return DMW3Save(c.extract_payload(loc))


def test_card_names_match_anchors():
    """The two live-verified anchors must resolve to the right names."""
    assert TABLES.card_name(0) == "Sacred Spear"
    assert TABLES.card_name(50) == "White Remove"


def test_card_names_rom_verified_corrections():
    """Names corrected 2026-09-02 against ROM uscardnm.toml must stay fixed."""
    fixed = {
        2: "Gold Aura",
        3: "Protect Aura",
        12: "Wield Aura",
        18: "Volcanic Cannon",
        24: "Darkness Gale",
        27: "Vicious Hacking",
        91: "Gururumon",
        146: "Omnimon II",
        150: "GranKuwagamon",
        159: "Lillymon",
        189: "Omnimon I",
        192: "Imperialdramon I",
        197: "Gryphonmon",
        198: "Paildramon I",
        240: "Creepymon",
        242: "Infermon",
        303: "Drimogemon",
        304: "NiseDrimogemon",
    }
    for idx, expect in fixed.items():
        assert TABLES.card_name(idx) == expect, f"card {idx}"
    # regression: the FAQ clip must never reappear
    names = [TABLES.card_name(i) for i in range(314)]
    assert "Gold Aur" not in names and "Sacred spear" not in names
    assert "Volcanic Gatlin" not in names and "Darness Gale" not in names
    assert len(TABLES.card) == 314


def test_card_reads_match_known_collection(usa_save):
    """Card counts at 0x06A3 must be in 0..9 (the collection)."""
    for i in range(0, CARD_COUNT, 7):
        assert 0 <= usa_save.card_count(i) <= 9


def test_card_write_recomputes_chunk2():
    """Setting a card must keep chunk 2 (and chunk 1) checksums valid."""
    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    s = DMW3Save(bytearray(c.extract_payload(loc)))
    old = s.card_count(0)
    s.set_card_count(0, (old + 1) % 10)
    out = s.to_bytes()
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)
    assert out[CARD_BASE] == (old + 1) % 10


def test_card_bounds_rejected(usa_save):
    with pytest.raises(SaveError):
        usa_save.set_card_count(-1, 1)
    with pytest.raises(SaveError):
        usa_save.set_card_count(CARD_COUNT, 1)
    with pytest.raises(SaveError):
        usa_save.set_card_count(0, 10)  # max is 9


def test_all_cards_zero_and_max(usa_save):
    s = usa_save
    s.set_all_cards(0)
    for i in (0, 100, 313):
        assert s.card_count(i) == 0
    s.set_all_cards(9)
    assert all(s.card_count(i) == 9 for i in (0, 1, 100, 313))
    out = s.to_bytes()
    assert ck.verify_chunk2(out)


def test_maxed_card_set_roundtrips_bytes():
    """The exact-314-nines pattern must survive load->set->to_bytes."""
    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    payload = bytearray(c.extract_payload(loc))
    s = DMW3Save(payload)
    s.set_all_cards(9)
    out = s.to_bytes()
    assert all(out[CARD_BASE + i] == 9 for i in range(CARD_COUNT))
