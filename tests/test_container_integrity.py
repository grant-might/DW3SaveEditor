"""Container-level integrity: editing a save must not disturb the file around it.

A .gme is 134,976 bytes (3904-byte DexDrive header + 131,072-byte card). An
editor that silently drops the header, or rewrites the card size, produces a file
the user's tools no longer recognise - so these properties are pinned here.
"""

import pathlib
import shutil
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import memcard as mc
from dmw3editor.core.save import DMW3Save

CARDS = pathlib.Path(
    r"C:\Users\space\Downloads\duckstation-windows-x64-release"
    r"\Digimon World 3 saves"
)
GME = CARDS / "digimon-world-3.21060.gme"      # DexDrive, USA
RAW = CARDS / "digimon-world-3.24459.gme"      # raw 128 KiB card, EUR


def _copy(tmp_path, src):
    if not src.exists():
        pytest.skip(f"{src.name} not present on this machine")
    dst = tmp_path / src.name
    shutil.copy2(src, dst)
    return dst


@pytest.mark.parametrize("src,expected_size", [(GME, 134976), (RAW, 131072)])
def test_file_size_is_preserved_exactly(tmp_path, src, expected_size):
    path = _copy(tmp_path, src)
    assert path.stat().st_size == expected_size

    card = mc.MemoryCard.load(str(path))
    loc = card.find_dmw3_save()
    save = DMW3Save(card.extract_payload(loc))
    save.set_money(0, 777)
    card.reinsert_payload(save.to_bytes(), loc)
    card.save(str(path))

    assert path.stat().st_size == expected_size


def test_dexdrive_header_is_preserved_byte_for_byte(tmp_path):
    path = _copy(tmp_path, GME)
    original_header = GME.read_bytes()[:3904]

    card = mc.MemoryCard.load(str(path))
    loc = card.find_dmw3_save()
    save = DMW3Save(card.extract_payload(loc))
    save.set_money(0, 4242)
    card.reinsert_payload(save.to_bytes(), loc)
    card.save(str(path))

    assert path.read_bytes()[:3904] == original_header


@pytest.mark.parametrize("src", [GME, RAW])
def test_a_single_field_edit_changes_only_a_handful_of_bytes(tmp_path, src):
    path = _copy(tmp_path, src)
    before = path.read_bytes()

    card = mc.MemoryCard.load(str(path))
    loc = card.find_dmw3_save()
    save = DMW3Save(card.extract_payload(loc))
    save.set_money(0, 12345)
    card.reinsert_payload(save.to_bytes(), loc)
    card.save(str(path))

    after = path.read_bytes()
    changed = [i for i in range(len(before)) if before[i] != after[i]]
    # 4 money bytes + at most 2 checksum bytes.
    assert len(changed) <= 6, [hex(c) for c in changed]


@pytest.mark.parametrize("src", [GME, RAW])
def test_no_op_edit_leaves_the_file_byte_identical(tmp_path, src):
    path = _copy(tmp_path, src)
    before = path.read_bytes()

    card = mc.MemoryCard.load(str(path))
    loc = card.find_dmw3_save()
    card.reinsert_payload(DMW3Save(card.extract_payload(loc)).to_bytes(), loc)
    card.save(str(path))

    assert path.read_bytes() == before


@pytest.mark.parametrize("src", [GME, RAW])
def test_other_directory_entries_are_untouched(tmp_path, src):
    """Editing DMW3 must not disturb other games' saves on the same card."""
    path = _copy(tmp_path, src)
    card = mc.MemoryCard.load(str(path))
    before = [(e.name, e.state, e.size) for e in card.directory()]

    loc = card.find_dmw3_save()
    save = DMW3Save(card.extract_payload(loc))
    save.set_money(0, 999)
    card.reinsert_payload(save.to_bytes(), loc)
    card.save(str(path))

    after = [(e.name, e.state, e.size) for e in mc.MemoryCard.load(str(path)).directory()]
    assert after == before
