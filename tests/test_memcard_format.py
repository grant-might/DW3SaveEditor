"""Memory-card save format — pinned against the matching decompilation.

Authority: the byte-matching decompilation DW3-DECOMP
(``include/stgmcard.h``, ``src/main/memcard.c``, ``src/stgmcard/stgmcard.c``),
cross-checked against the real USA and European sample cards. Every assertion
here is falsifiable and pins a fact the editor relies on.

Offsets are payload-absolute within the 32,768-byte DMW3 file.
"""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import checksum as ck
from dmw3editor.core import memcard as mc
from dmw3editor.core.save import (
    DATA_SECTION_OFFSETS,
    DATA_SECTION_SIZE,
    DIGI_STAT_BASE,
    DIGI_STAT_BASE_REL,
    DIGI_STAT_STRIDE,
    DMW3Save,
    D_LEVEL,
    D_UNLOCK,
    F_AREA,
    F_HOURS,
    F_MINUTES,
    F_MONEY,
    F_NAME,
    F_NAME_SIZE,
    F_PARTY_IDS,
    F_PARTY_LEVELS,
    F_SECONDS,
    F_SHOP,
    F_TIME_FRAMES,
    F_TIME_MAXED,
    F_UNK42,
    GAME_SAVE_SIZE_BY_VERSION,
    GS_PARTY,
    H_CHECKSUM,
    H_LAST,
    H_UNK3,
    H_VERSION,
    INFO_SECTION_SIZE,
    MAGIC_OFFSET,
    SLOT_OFFSETS,
    SLOT_SIZE,
    party_id_for_index,
    party_index_for_id,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def bin_payload(name: str) -> bytearray:
    """A sample's already-extracted 32 KiB payload."""
    return bytearray((ROOT / "samples" / name).read_bytes())


def card_payload(name: str) -> bytearray:
    """A sample card's payload, extracted through the container layer."""
    c = mc.MemoryCard.load(str(ROOT / "samples" / name))
    return bytearray(c.extract_payload(c.find_dmw3_save()))


# ---- info section (MemCardFile) header -----------------------------------
def test_info_header_is_byte_fields_not_u16():
    """stgmcard.h: u8 checksum, u8 last, u8 version, u8 unk3, s32 magic."""
    assert (H_CHECKSUM, H_LAST, H_VERSION, H_UNK3, MAGIC_OFFSET) == (
        0x0200, 0x0201, 0x0202, 0x0203, 0x0204,
    )
    for name, ver in (("USA_save.bin", 3), ("EUR_save.bin", 4)):
        d = bin_payload(name)
        assert d[H_VERSION] == ver
        assert ck.region_version(d) == ver
        assert ck.format_version(d) == ver   # a byte, not the little-endian u16
        assert d[H_UNK3] == 0
        assert d[MAGIC_OFFSET:MAGIC_OFFSET + 4] == b"DMW3"


def test_chunk1_covers_memcardfile_minus_its_first_four_bytes():
    """memcard.c: checksum over [magic, sizeof(MemCardFile)) == [0x204, 0x2D4)."""
    assert ck.COVERED_START == 0x0204
    assert ck.MEMCARD_FILE_SIZE == 0x00D4
    assert ck.COVERED_END == 0x02D4
    assert ck.COVERED_END - ck.COVERED_START == ck.MEMCARD_FILE_SIZE - 4
    # the last slot ends exactly at the end of MemCardFile
    assert SLOT_OFFSETS[-1] + SLOT_SIZE == ck.COVERED_END
    # [0x2D4, 0x300) is zero padding: covering to 0x300 would be equivalent
    for name in ("USA_save.bin", "EUR_save.bin"):
        d = bin_payload(name)
        assert all(b == 0 for b in d[0x02D4:0x0300])
        assert ck.verify_header(d)
        assert ck.stored_header_checksum(d) == ck.xor8(d[0x0204:0x02D4])
        assert ck.stored_header_checksum(d) < 0x100   # a byte, not a u16


def test_recompute_header_preserves_the_last_saved_slot_byte():
    """The checksum is 1 byte; 0x0201 (last) must survive a save."""
    d = bin_payload("USA_save.bin")
    d[H_LAST] = 2
    d[0x0240] ^= 0x01                # an in-slot byte -> forces a changed checksum
    out = bytearray(DMW3Save(bytes(d)).to_bytes())
    assert out[H_LAST] == 2, "recompute clobbered MemCardFile.last"
    assert ck.verify_header(out)


# ---- MemCardSave layout --------------------------------------------------
def test_memcard_save_layout_matches_decomp():
    """stgmcard.h MemCardSave, 0x44 bytes; three records after the 8-byte head."""
    assert (F_NAME, F_NAME_SIZE) == (0x00, 0x18)
    assert (F_AREA, F_SHOP) == (0x18, 0x1C)
    assert F_MONEY == 0x20
    assert F_TIME_FRAMES == 0x24
    assert (F_HOURS, F_MINUTES, F_SECONDS, F_TIME_MAXED) == (0x28, 0x2A, 0x2C, 0x2E)
    assert F_PARTY_IDS == (0x30, 0x34, 0x38)
    assert F_PARTY_LEVELS == (0x3C, 0x3E, 0x40)
    assert F_UNK42 == 0x42
    assert SLOT_SIZE == 0x44
    assert SLOT_OFFSETS == (0x0208, 0x024C, 0x0290)
    assert SLOT_OFFSETS[0] == 0x0208            # right after checksum/last/ver/unk3/tag


def test_slot_properties_read_their_decomp_offsets():
    d = bin_payload("USA_save.bin")
    s = DMW3Save(bytes(d)).slots[0]
    base = SLOT_OFFSETS[0]
    assert s.area_id == struct.unpack_from("<I", bytes(d), base + F_AREA)[0]
    assert s.shop_id == struct.unpack_from("<I", bytes(d), base + F_SHOP)[0]
    assert s.money == struct.unpack_from("<I", bytes(d), base + F_MONEY)[0]
    assert s.play_frames == struct.unpack_from("<i", bytes(d), base + F_TIME_FRAMES)[0]
    assert s.play_time_maxed == struct.unpack_from("<h", bytes(d), base + F_TIME_MAXED)[0]
    assert s.unk42 == struct.unpack_from("<h", bytes(d), base + F_UNK42)[0]
    assert s.party == [
        (struct.unpack_from("<I", bytes(d), base + off)[0], lv)
        for off, lv in zip(F_PARTY_IDS, [struct.unpack_from("<h", bytes(d), base + o)[0]
                                         for o in F_PARTY_LEVELS])
    ]
    assert len(s.name_bytes) == 0x18
    # stgmcard.c:167-168: 0x18 is the AREA index and 0x1C the SHOP index.
    # partner_id is only the legacy alias for area_id.
    assert s.partner_id == s.area_id


# ---- data sections (GameSave) + region-dependent checksum ----------------
def test_data_section_geometry_matches_initMemCard():
    """system.c: MEMCARD.infoSize = 0x100, MEMCARD.dataSize = 0x2700."""
    assert INFO_SECTION_SIZE == 0x100
    assert DATA_SECTION_SIZE == 0x2700
    assert DATA_SECTION_OFFSETS == (0x0300, 0x2A00, 0x5100)
    assert DATA_SECTION_OFFSETS[0] == ck.HEADER_OFFSET + INFO_SECTION_SIZE
    for a, b in zip(DATA_SECTION_OFFSETS, DATA_SECTION_OFFSETS[1:]):
        assert b - a == DATA_SECTION_SIZE
    # each section carries its own u8 checksum + u8 version header
    for name, ver in (("USA_save.bin", 3), ("EUR_save.bin", 4)):
        d = bin_payload(name)
        assert d[DATA_SECTION_OFFSETS[0] + 2] == ver
    usa = bin_payload("USA_save.bin")
    for off in DATA_SECTION_OFFSETS:      # all three slots used on the USA sample
        assert usa[off + 2] == 3


def test_chunk2_extent_is_region_dependent():
    """stgmcard.h: GAME_SAVE_SIZE 0x26BC USA / 0x26C4 EUR -> ends 0x29BC / 0x29C4."""
    assert GAME_SAVE_SIZE_BY_VERSION == {3: 0x26BC, 4: 0x26C4}
    assert ck.CHUNK2_COVERED_END_USA == 0x29BC
    assert ck.CHUNK2_COVERED_END == 0x29C4
    assert ck.chunk2_covered_end(bin_payload("USA_save.bin")) == 0x29BC
    assert ck.chunk2_covered_end(bin_payload("EUR_save.bin")) == 0x29C4


def test_chunk2_verifies_on_both_regions_and_both_containers():
    assert ck.verify_chunk2(bin_payload("USA_save.bin"))
    assert ck.verify_chunk2(bin_payload("EUR_save.bin"))
    assert ck.verify_chunk2(card_payload("USA_dexdrive.gme"))
    assert ck.verify_chunk2(card_payload("EUR_raw.mcr"))


def test_usa_and_eur_extents_differ_observably():
    """The region rule is not cosmetic: a byte in [0x29BC, 0x29C4) is uncovered
    on a USA card, so the old fixed 0x29C4 rule would mis-verify it."""
    d = bin_payload("USA_save.bin")
    assert all(b == 0 for b in d[0x29BC:0x29C4])
    d[0x29BC] = 0x7F
    assert ck.verify_chunk2(d), "byte outside the USA range changed the checksum"
    assert ck.stored_chunk2_checksum(d) == ck.xor8(d[0x0304:0x29BC])
    assert ck.xor8(d[0x0304:0x29C4]) != ck.stored_chunk2_checksum(d)


def test_checksum_bytes_are_not_clobbering_neighbours():
    """Writing both checksums must leave the adjacent u8 fields intact."""
    d = bin_payload("EUR_save.bin")
    d[H_LAST] = 1
    d[0x0301] = 0x5A          # the unused byte after the section checksum
    out = bytearray(DMW3Save(bytes(d)).to_bytes())
    assert out[H_LAST] == 1
    assert out[0x0301] == 0x5A
    assert ck.verify_all(out)


# ---- the party is stored TWICE; a swap must write BOTH --------------------
def test_game_loads_party_from_the_data_section_not_the_summary():
    """The running party comes from the data section, not the info summary.

    stgmcard.c:1027  *(GameSave *)&GAME = *(GameSave *)STGMCard_funcs.dataBuf;
    game_state.h:297 /* 0x0070 */ s32 party[3]; /* partner indices */
    stgmcard.c:1106  save->partners[i] = dataBuf->partners[member].unlocked;
    """
    assert GS_PARTY == 0x0070
    assert DATA_SECTION_OFFSETS[0] + GS_PARTY == 0x0370
    assert DATA_SECTION_OFFSETS[0] + DIGI_STAT_BASE_REL == DIGI_STAT_BASE == 0x0A48
    # the summary partners[] hold ids (Partner.unlocked = index + 3); the data
    # section holds the index itself, so a conversion is required.
    assert party_id_for_index(7, "USA") == 10
    assert party_index_for_id(10, "USA") == 7
    assert party_index_for_id(10, "EUR") == 7


def test_party_swap_writes_summary_id_AND_data_section_index():
    """One swap must land in both copies, region-aware, on either region."""
    for name, ver in (("USA_save.bin", 3), ("EUR_save.bin", 4)):
        save = DMW3Save(bytes(bin_payload(name)))
        assert save.version == ver
        save.set_party_member(0, 2, 10, 42)     # Patamon, id 10 -> index 7
        out = save.to_bytes()
        # (1) summary: id + level
        assert struct.unpack_from("<i", out, SLOT_OFFSETS[0] + F_PARTY_IDS[2])[0] == 10
        assert struct.unpack_from("<h", out, SLOT_OFFSETS[0] + F_PARTY_LEVELS[2])[0] == 42
        # (2) data section: the INDEX the game loads, not the id
        assert save.party_indices(0)[2] == 7
        assert struct.unpack_from("<i", out, DATA_SECTION_OFFSETS[0] + GS_PARTY + 8)[0] == 7
        # the partner is unlocked (so getPartyPartner accepts it) and levelled
        pb = DATA_SECTION_OFFSETS[0] + DIGI_STAT_BASE_REL + 7 * DIGI_STAT_STRIDE
        assert struct.unpack_from("<i", out, pb + D_UNLOCK)[0] == 10
        assert struct.unpack_from("<H", out, pb + D_LEVEL)[0] == 42
        assert DMW3Save(out).checksum_valid


def test_party_swap_is_idempotent_and_reopens_consistently():
    save = DMW3Save(bytes(bin_payload("USA_save.bin")))
    save.set_party_member(0, 0, 8, 60)          # Guilmon id 8 -> index 5
    once = save.to_bytes()
    assert save.party_indices(0)[0] == 5
    again = DMW3Save(once)
    assert again.slots[0].party[0] == (8, 60)
    assert again.party_indices(0)[0] == 5
    again.set_party_member(0, 0, 8, 60)
    assert again.to_bytes() == once


def test_data_section_party_write_is_skipped_for_forbidden_slots():
    """In-game slots 2/3 have no writable data section yet: no exception, and
    the summary is still updated."""
    save = DMW3Save(bytes(bin_payload("USA_save.bin")))
    assert not save.party_data_written(1)
    before = save.party_indices(1)
    save.set_party_member(1, 0, 7, 33)
    assert save.party_indices(1) == before      # data section untouched
    assert save.slots[1].party[0][0] == 7       # summary did change
