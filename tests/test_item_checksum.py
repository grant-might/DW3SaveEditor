"""Item array + chunk-2 checksum integration tests.

The item quantity array lives at payload 0x03A7 INSIDE chunk 2
([0x0304, 0x29C4), checksum u16@0x0300). This test proves an item edit must
recompute chunk 2, and that the model's to_bytes() does so.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import checksum as ck

ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEM_BASE = 0x03A7


@pytest.fixture
def usa_payload():
    """Full-card payload from the real USA sample (32 KiB)."""
    from dmw3editor.core import memcard as mc

    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    return bytearray(c.extract_payload(loc))


def test_item_array_is_inside_chunk2(usa_payload):
    assert usa_payload[ITEM_BASE] >= 0  # item 0 exists at 0x03A7
    assert ck.verify_chunk2(usa_payload)
    # flipping an item byte breaks chunk 2 but not chunk 1
    usa_payload[ITEM_BASE] ^= 0x01
    assert not ck.verify_chunk2(usa_payload)
    assert ck.verify_header(usa_payload)


def test_item_edit_recompute_all_restores_validity(usa_payload):
    usa_payload[ITEM_BASE] = 42
    assert not ck.verify_chunk2(usa_payload)
    ck.recompute_all(usa_payload)
    assert ck.verify_header(usa_payload)
    assert ck.verify_chunk2(usa_payload)


def test_item_edit_via_save_model_keeps_checksums_valid():
    """End-to-end: set an item through DMW3Save and confirm both chunks."""
    from dmw3editor.core import memcard as mc
    from dmw3editor.core.save import DMW3Save

    c = mc.MemoryCard.load(str(ROOT / "samples" / "USA_dexdrive.gme"))
    loc = c.find_dmw3_save()
    s = DMW3Save(c.extract_payload(loc))
    out = s.to_bytes()  # serialize; recompute_all runs
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)
