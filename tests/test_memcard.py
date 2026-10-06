"""Tests for dmw3editor.core.memcard (PS1 memory-card container I/O).

Run with the project venv interpreter:
    D:/AGENT/DMW3SaveEditor/.venv/Scripts/python.exe -m pytest tests -q

`samples/` is READ-ONLY; all mutations happen on copies in a temp dir.
"""
import os
import tempfile

import numpy as np
import pytest

from dmw3editor.core.memcard import (
    ContainerFormat,
    MemoryCard,
    detect_format,
    extract_dmw3_payload,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "samples")

EUR_MCR = os.path.join(SAMPLES, "EUR_raw.mcr")          # raw, 131072 B
USA_GME = os.path.join(SAMPLES, "USA_dexdrive.gme")      # DexDrive, 134976 B
EUR_BIN = os.path.join(SAMPLES, "EUR_save.bin")          # orchestrator-extracted payload
USA_BIN = os.path.join(SAMPLES, "USA_save.bin")


def _orig_bytes(path):
    with open(path, "rb") as f:
        return f.read()


# --------------------------------------------------------------------------
# 1. Container detection
# --------------------------------------------------------------------------
def test_detect_raw():
    fmt, hdr = detect_format(_orig_bytes(EUR_MCR))
    assert fmt is ContainerFormat.RAW
    assert hdr == 0


def test_detect_gme():
    fmt, hdr = detect_format(_orig_bytes(USA_GME))
    assert fmt is ContainerFormat.GME
    assert hdr == 3904


def test_detect_bad_size_raises():
    with pytest.raises(ValueError):
        detect_format(b"\x00" * 1000)


# --------------------------------------------------------------------------
# 2. Region detection + save location (CONFIRMED prefixes)
# --------------------------------------------------------------------------
def test_region_eur():
    mc = MemoryCard.load(EUR_MCR)
    loc = mc.find_dmw3_save()
    assert loc is not None
    assert loc.region == "EUR"
    assert loc.name == "BESLES-03936DMW3-EUR"
    assert loc.chain == [1, 2, 3, 4]
    assert loc.size == 32768


def test_region_usa():
    mc = MemoryCard.load(USA_GME)
    loc = mc.find_dmw3_save()
    assert loc is not None
    assert loc.region == "USA"
    assert loc.name == "BASLUS-01436DMW3-USA"
    assert loc.chain == [1, 2, 3, 4]
    assert loc.size == 32768


# --------------------------------------------------------------------------
# 3. Extraction matches the orchestrator's reference payloads (cross-check)
# --------------------------------------------------------------------------
def test_extract_matches_reference_eur():
    payload, loc = extract_dmw3_payload(EUR_MCR)
    ref = _orig_bytes(EUR_BIN)
    assert payload == ref
    assert len(payload) == 32768


def test_extract_matches_reference_usa():
    payload, loc = extract_dmw3_payload(USA_GME)
    ref = _orig_bytes(USA_BIN)
    assert payload == ref
    assert len(payload) == 32768


# --------------------------------------------------------------------------
# 4. BYTE-EXACT round-trip: load -> extract -> reinsert -> compare identical
#    On BOTH samples, in their ORIGINAL container format.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("path", [EUR_MCR, USA_GME],
                         ids=["EUR_raw_mcr", "USA_dexdrive_gme"])
def test_byte_exact_roundtrip(path):
    original = _orig_bytes(path)
    mc = MemoryCard.load(path)
    loc = mc.find_dmw3_save()
    payload = mc.extract_payload(loc)

    # Reinsert the SAME payload and save -> must equal the original file.
    tmp = tempfile.mktemp(suffix=".bin")
    try:
        mc.reinsert_payload(payload, loc)
        mc.save(tmp)
        result = _orig_bytes(tmp)
        assert result == original, "round-trip not byte-exact"
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --------------------------------------------------------------------------
# 5. Modification path: a changed payload is written back, then restoring it
#    returns to the original bytes (proves reinsert actually writes blocks and
#    the unmodified regions stay byte-identical).
# --------------------------------------------------------------------------
@pytest.mark.parametrize("path", [EUR_MCR, USA_GME],
                         ids=["EUR_raw_mcr", "USA_dexdrive_gme"])
def test_modify_then_restore(path):
    original = _orig_bytes(path)
    mc = MemoryCard.load(path)
    loc = mc.find_dmw3_save()
    payload = bytearray(mc.extract_payload(loc))

    # Flip one game-data byte (0x200 is the first live game byte).
    payload[0x200] ^= 0xFF
    tmp = tempfile.mktemp(suffix=".bin")
    try:
        mc.reinsert_payload(bytes(payload), loc)
        mc.save(tmp)
        assert _orig_bytes(tmp) != original          # changed -> differs
        # Restore and re-save -> byte-exact again.
        mc2 = MemoryCard.load(tmp)
        loc2 = mc2.find_dmw3_save()
        restored = bytearray(mc2.extract_payload(loc2))
        restored[0x200] ^= 0xFF
        mc2.reinsert_payload(bytes(restored), loc2)
        tmp2 = tempfile.mktemp(suffix=".bin")
        try:
            mc2.save(tmp2)
            assert _orig_bytes(tmp2) == original
        finally:
            if os.path.exists(tmp2):
                os.remove(tmp2)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --------------------------------------------------------------------------
# 6. Title-frame parsing (SC magic, flags, Shift-JIS title, CLUT, icon)
# --------------------------------------------------------------------------
def test_title_eur():
    mc = MemoryCard.load(EUR_MCR)
    tf = mc.parse_title()
    assert tf.magic == "SC"
    assert tf.icon_flags == 0x13
    assert tf.icon_count == 4
    assert tf.title == "ＤＷ２００３"
    assert tf.clut.shape == (16, 3)
    assert tf.icon_frames.shape == (4, 16, 16, 3)
    # First CLUT entry is 0x0000 -> transparent black.
    assert tuple(int(v) for v in tf.clut[0]) == (0, 0, 0)
    # Icon is not blank.
    assert tf.icon_frames.sum() > 0


def test_title_usa():
    mc = MemoryCard.load(USA_GME)
    tf = mc.parse_title()
    assert tf.magic == "SC"
    assert tf.icon_flags == 0x13
    assert tf.icon_count == 4
    assert tf.title.startswith("Ｄｉｇｉｍｏｎ")
    assert tf.title == "Ｄｉｇｉｍｏｎ　Ｗｏｒｌｄ　３　Ｓａｖｅｄ　Ｄａ"
    assert tf.clut.shape == (16, 3)
    assert tf.icon_frames.shape == (4, 16, 16, 3)
    assert tuple(int(v) for v in tf.clut[0]) == (0, 0, 0)
    assert tf.icon_frames.sum() > 0


# --------------------------------------------------------------------------
# 7. VGS / VMP containers -- UNTESTED against a real file.
#    These synthetic containers are built by prepending a 128-byte header to the
#    REAL EUR card body, purely to exercise the detect/strip/reinsert code path
#    and prove header preservation.  No real .vgs/.vmp dump was available, so
#    the *format* is unverified -- only the round-trip logic is tested here.
# --------------------------------------------------------------------------
def _synthetic_container(body_path, header: bytes):
    body = _orig_bytes(body_path)
    assert len(body) == 131072
    assert len(header) == 128
    return header + body


@pytest.mark.parametrize("kind,header", [
    ("vgs", b"\x00" * 128),
    ("vmp", b"VMP" + b"\x00" * 125),
], ids=["vgs_synthetic", "vmp_synthetic"])
def test_synthetic_vgs_vmp_roundtrip(kind, header):
    synth = _synthetic_container(EUR_MCR, header)
    fmt, hdr_len = detect_format(synth)
    assert fmt is (ContainerFormat.VGS if kind == "vgs" else ContainerFormat.VMP)
    assert hdr_len == 128

    mc = MemoryCard(synth)
    loc = mc.find_dmw3_save()
    assert loc is not None
    assert loc.region == "EUR"

    payload = mc.extract_payload(loc)
    ref = _orig_bytes(EUR_BIN)
    assert payload == ref

    # Reinsert + save -> byte-exact vs the synthetic original (header preserved).
    tmp = tempfile.mktemp(suffix=".bin")
    try:
        mc.reinsert_payload(payload, loc)
        mc.save(tmp)
        assert _orig_bytes(tmp) == synth
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_all_three_regions_including_jpn_are_recognised():
    """JPN id confirmed from SLES_039.36 at 0x9FC (no JPN sample card exists)."""
    from dmw3editor.core.memcard import DMW3_PREFIXES
    assert DMW3_PREFIXES["BASLUS-01436"] == "USA"
    assert DMW3_PREFIXES["BESLES-03936"] == "EUR"
    assert DMW3_PREFIXES["BISLPS-03446"] == "JPN"


def test_region_ids_present_in_game_executable():
    """Cross-check our region table against the game's own binary."""
    import pathlib
    exe = pathlib.Path(__file__).resolve().parents[1] / "work" / "disc_extract" / "SLES_039.36"
    if not exe.exists():
        import pytest
        pytest.skip("disc not extracted")
    blob = exe.read_bytes()
    assert blob.find(b"BISLPS-03446DMW3-JPN") == 0x9FC
    assert blob.find(b"BASLUS-01436DMW3-USA") == 0xA14
    assert blob.find(b"BESLES-03936DMW3-EUR") == 0xA2C
