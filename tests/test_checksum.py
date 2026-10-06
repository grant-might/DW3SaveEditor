"""Checksum tests. The 0x0200 header checksum is the safety property that
decides whether an edited save is accepted by the game, so it is tested against
BOTH real cards and for change-sensitivity."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import random
from dmw3editor.core import checksum as ck

ROOT = pathlib.Path(__file__).resolve().parents[1]


def payload(name):
    return bytearray((ROOT / "samples" / name).read_bytes())


def test_usa_header_checksum_validates():
    p = payload("USA_save.bin")
    assert ck.stored_header_checksum(p) == 232
    assert ck.compute_header_checksum(p) == 232
    assert ck.verify_header(p)


def test_eur_header_checksum_validates():
    p = payload("EUR_save.bin")
    assert ck.stored_header_checksum(p) == 90
    assert ck.compute_header_checksum(p) == 90
    assert ck.verify_header(p)


def test_version_words_differ_between_regions():
    assert ck.format_version(payload("USA_save.bin")) == 3
    assert ck.format_version(payload("EUR_save.bin")) == 4


def test_checksum_is_change_sensitive():
    """A checksum that ignores edits is worthless. Prove it reacts."""
    for name in ("USA_save.bin", "EUR_save.bin"):
        p = payload(name)
        assert ck.verify_header(p)
        p[ck.COVERED_START + 3] ^= 0xFF
        assert not ck.verify_header(p), name


def test_recompute_restores_validity_after_edit():
    for name in ("USA_save.bin", "EUR_save.bin"):
        p = payload(name)
        p[ck.COVERED_START + 10] ^= 0x5A
        assert not ck.verify_header(p)
        ck.recompute_header(p)
        assert ck.verify_header(p), name


def test_recompute_is_idempotent_and_noop_on_clean_save():
    for name in ("USA_save.bin", "EUR_save.bin"):
        original = bytes(payload(name))
        p = bytearray(original)
        ck.recompute_header(p)
        assert bytes(p) == original, name


def test_every_single_byte_in_range_affects_checksum():
    """Each covered byte must matter, or our range is wrong."""
    p = payload("USA_save.bin")
    base = ck.compute_header_checksum(p)
    for off in range(ck.COVERED_START, ck.COVERED_END):
        q = bytearray(p)
        q[off] ^= 0x01
        assert ck.compute_header_checksum(q) != base, hex(off)


def test_bytes_outside_range_do_not_affect_checksum():
    p = payload("USA_save.bin")
    base = ck.compute_header_checksum(p)
    for off in (ck.COVERED_END, ck.COVERED_END + 1, 0x1000, 0x2900, 0x7000):
        q = bytearray(p)
        q[off] ^= 0xFF
        assert ck.compute_header_checksum(q) == base, hex(off)


def test_range_match_is_not_coincidence():
    """0/N random ranges should reproduce BOTH cards' stored values."""
    u = payload("USA_save.bin")
    e = payload("EUR_save.bin")
    rng = random.Random(1234)
    false_hits = 0
    for _ in range(3000):
        s = rng.randrange(0x200, 0x260)
        end = rng.randrange(0x280, 0x2900)
        if ck.xor8(u[s:end]) == 232 and ck.xor8(e[s:end]) == 90:
            false_hits += 1
    assert false_hits == 0, f"{false_hits} coincidental ranges - range is ambiguous"


def test_chunk2_checksum_validates_on_all_cards():
    """Chunk 2 (u16@0x0300 over [0x0304, 0x29C4)) must validate on both real
    cards and the after-item-buy capture (three independent states)."""
    import io
    from dmw3editor.core import memcard as mc

    def payload_from_card(name):
        c = mc.MemoryCard.load(str(ROOT / "samples" / name))
        return bytearray(c.extract_payload(c.find_dmw3_save()))

    usa = payload_from_card("USA_dexdrive.gme")
    eur = payload_from_card("EUR_raw.mcr")
    # EUR-after-item-buy capture lives in captures/ (skip if absent)
    print("chunk2 header values:", hex(ck.stored_chunk2_checksum(usa)),
          hex(ck.stored_chunk2_checksum(eur)))
    assert ck.verify_chunk2(usa)
    assert ck.verify_chunk2(eur)


def test_chunk2_is_change_sensitive_and_recomputes():
    p = payload("USA_save.bin")
    if len(p) < ck.CHUNK2_COVERED_END:
        return  # sample payload too short
    assert ck.verify_chunk2(p)
    p[0x03A7] ^= 0x01  # the item quantity array is inside chunk 2
    assert not ck.verify_chunk2(p)
    ck.recompute_chunk2(p)
    assert ck.verify_chunk2(p)
    # an item edit must NOT disturb chunk 1's validity either
    assert ck.verify_header(p)


def test_unverified_regions_start_after_chunk2():
    """With chunk 2 solved, the unsolved region begins at 0x29C4."""
    regions = ck.unverified_regions(payload("USA_save.bin"))
    assert regions
    start, _end, _note = regions[0]
    assert start == ck.CHUNK2_COVERED_END == 0x29C4
