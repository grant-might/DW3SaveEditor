"""Tests for the save model — every assertion pinned to real card bytes."""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import checksum as ck
from dmw3editor.core.save import (
    D_DV_COUNT,
    D_DV_HEADER,
    D_DV_MAX,
    D_DV_SLOT_CONTENT,
    D_DV_SLOT_CONTENT_LEN,
    D_DV_SLOT_CONTENT_PHANTOM,
    D_DV_SLOT_LEVEL,
    D_DV_SLOTS,
    D_DV_SLOT_STRIDE,
    DV_FORM_MARKERS,
    D_EXP,
    D_HP,
    D_LEVEL,
    D_STATS,
    DIGI_MAX_EXP,
    DIGI_MAX_HP,
    DIGI_MAX_STAT,
    DIGI_ROSTER_NAMES,
    DIGI_STAT_BASE,
    DIGI_STAT_COUNT,
    DIGI_STAT_STRIDE,
    DMW3Save,
    ITEM_BASE,
    KEY_ITEM_COUNT,
    MONEY_MAX,
    SLOT_OFFSETS,
    TABLES,
    SaveError,
    dv_tech_content,
    key_item_offset,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    return DMW3Save((ROOT / "samples" / name).read_bytes())


@pytest.fixture
def usa():
    return load("USA_save.bin")


@pytest.fixture
def eur():
    return load("EUR_save.bin")


# ---- identity ------------------------------------------------------------
def test_regions_and_versions(usa, eur):
    assert (usa.version, usa.region_guess) == (3, "USA")
    assert (eur.version, eur.region_guess) == (4, "EUR")


def test_both_samples_have_valid_checksums(usa, eur):
    assert usa.checksum_valid
    assert eur.checksum_valid


def test_rejects_non_dmw3_payload():
    junk = bytearray(32768)
    with pytest.raises(SaveError, match="not a Digimon World 3 save"):
        DMW3Save(junk)


def test_region_override_roundtrip(usa, eur):
    """force_region / clear_region_override steer region_guess without
    touching the payload (used by the ROM-region selector)."""
    assert usa.region_guess == "USA"
    usa.force_region("EUR")
    assert usa.region_guess == "EUR"
    usa.clear_region_override()
    assert usa.region_guess == "USA"
    with pytest.raises(SaveError, match="unsupported region"):
        usa.force_region("JPN")
    # payload bytes are untouched by an override
    before = bytes(usa._buf)
    usa.force_region("EUR")
    assert bytes(usa._buf) == before


def test_rejects_wrong_size():
    with pytest.raises(SaveError, match="32768-byte payload"):
        DMW3Save(bytearray(1024))


# ---- decoded values, pinned to the real cards ---------------------------
def test_usa_slots_decode_exactly(usa):
    s = usa.slots
    assert [x.is_empty for x in s] == [False, False, False]
    assert [x.money for x in s] == [9_999_951] * 3
    # Three saves made a minute apart - proof these are separate slots.
    assert [x.play_time for x in s] == [
        (199, 43, 45),
        (199, 42, 43),
        (199, 41, 31),
    ]
    # Party ids reorder between slots; levels reorder in lockstep.
    assert s[0].party == [(6, 98), (7, 99), (8, 99)]
    assert s[1].party == [(7, 99), (8, 99), (6, 98)]
    assert s[2].party == [(8, 99), (7, 99), (6, 98)]
    assert s[0].partner_name == "Kumamon"


def test_eur_has_only_first_slot_used(eur):
    s = eur.slots
    assert [x.is_empty for x in s] == [False, True, True]
    assert s[0].money == MONEY_MAX == 9_999_999
    assert s[0].play_time == (20, 43, 36)
    # Raw party ids 6/7/8 are PARTY-space (Agumon/Veemon/Guilmon), NOT the
    # decomp enum. Confirmed by the user's in-game read of a 6/7/8 card.
    assert s[0].party == [(6, 99), (7, 99), (8, 99)]
    assert s[0].party_text == "Agumon Lv99, Veemon Lv99, Guilmon Lv99"
    assert s[0].partner_name == "Agumon"


def test_usa_party_ids_are_decomp_space(usa):
    # USA (v3) party field uses decomp ids directly: 6/7/8 = Guilmon/
    # Renamon/Patamon (this is the genuine DexDrive sample, unedited).
    names = {TABLES.party_name(i, "USA") for i, _ in usa.slots[0].party}
    assert names == {"Guilmon", "Renamon", "Patamon"}
    assert usa.slots[0].party_text == (
        "Guilmon Lv98, Renamon Lv99, Patamon Lv99"
    )


def test_eur_party_ids_are_shifted_plus_two(eur):
    # EUR (v4) party field is decomp id + 2: 6/7/8 = Agumon/Veemon/Guilmon.
    # Confirmed by the user's in-game read of a card with raw ids 6/7/8 and
    # by the user seeing Kotemon at raw id 3 (ids 1-2 render empty/invalid).
    names = {TABLES.party_name(i, "EUR") for i, _ in eur.slots[0].party}
    assert names == {"Agumon", "Veemon", "Guilmon"}


def test_eur_name_field_holds_ascii(eur):
    assert "5069" in eur.slots[0].name_ascii


def test_summary_mentions_every_slot(usa):
    text = usa.summary()
    assert "Slot 1" in text and "Slot 3" in text
    assert "9,999,951" in text
    assert "Guilmon" in text


# ---- id tables -----------------------------------------------------------
def test_id_tables_loaded_from_decompilation():
    assert len(TABLES.digimon) == 251
    # The save-ordered item table (352 slots: 49 items + 123 weapons + 77 armor
    # + 68 accessories + 35 card packs) replaces the 403-entry decomp enum.
    assert len(TABLES.item) == 352
    assert TABLES.digimon[1] == "Kotemon"
    assert TABLES.digimon[6] == "Guilmon"
    assert TABLES.item[0] == "Power Charge"       # save slot 0
    assert TABLES.item[49] == "Short Sword"       # first weapon
    assert TABLES.item[351] == "R-Booster 05"      # last save slot
    # Key-item table in Important-screen order (48 flags).
    assert len(TABLES.key_item) == 48
    assert TABLES.key_item[0] == "Tree Boots"
    assert TABLES.key_item[39] == "Monmon DDNA"
    assert TABLES.key_item[47] == "Folder Bag"
    # Card-pack table: all 35 packs, save slots verified by the player's
    # item-tab read-back (Booster 01a at 48, 02a-15a at 318-331, 1b-15b at
    # 332-346, R-Booster 01-05 at 347-351).
    assert len(TABLES.pack) == 35
    assert TABLES.pack_name(0) == "Booster 01a"
    assert TABLES.pack_name(14) == "Booster 15a"
    assert TABLES.pack_name(15) == "Booster 1b"
    assert TABLES.pack_name(29) == "Booster 15b"
    assert TABLES.pack_name(34) == "R-Booster 05"
    assert TABLES.pack_save_slot(0) == 48
    assert TABLES.pack_save_slot(1) == 318
    assert TABLES.pack_save_slot(15) == 332
    assert TABLES.pack_save_slot(30) == 347
    assert TABLES.pack_save_slot(34) == 351


def test_item_names_rom_verified_corrections():
    """Names corrected 2026-09-02 against ROM usitmnam.toml (slot N == table N+43).

    All 62 fixes are spacing/typos from the FAQ-era source; the important-item
    names (key_item table) are intentionally NOT in this list.
    """
    fixed = {
        19: "Train Chip 1",
        20: "Train Chip 2",
        21: "Train Chip 3",
        33: "DV Plug",
        47: "TNT Ball",
        48: "Booster 01a",
        203: "D-Tama Helmet",
        218: "King's Mantle",
        278: "EXP Adapter",
        279: "BIT Adapter",
        280: "MP Proxy",
        281: "MP Mega Proxy",
        282: "HP Proxy",
        283: "HP Mega Proxy",
        296: "Fire Power 1",
        302: "Ice Power 1",
        308: "Bolt Power 1",
        311: "Metal Power 1",
        314: "Dark Power 1",
        315: "Dark Power 2",
        318: "Booster 02a",
        347: "R-Booster 01",
        351: "R-Booster 05",
    }
    for idx, expect in fixed.items():
        assert TABLES.item[idx] == expect, f"item {idx}"
    # regression: no clipped run-together pack/proxy names anywhere
    bad = [TABLES.item[i] for i in range(352)
           if any(b in TABLES.item[i] for b in ("Booster01", "R-Booster0", "Adapter", "Proxy")) and
           any(c.isdigit() for c in TABLES.item[i]) and " " not in TABLES.item[i]]
    assert bad == [], bad


def test_key_item_names_are_region_aware():
    """EUR localization differs from USA in 11 Important-item names.

    The EUR English table (esitmnam.toml) left the 8 card-battle Tags and
    Recovery CD 3 as untranslated Japanese (CONFIRMED from the decompiled
    lang files + the player's EUR in-game screen 2026-09-02), and uses Koc
    Trophy / Platinum Card where the USA table says World Champ / Asuka
    Medal. Names identical for the other 37.
    """
    assert TABLES.key_item_name(0, "USA") == TABLES.key_item_name(0, "EUR") == "Tree Boots"
    assert TABLES.key_item_name(22, "USA") == "Seiryu Tag"
    eur_tag = TABLES.key_item_name(22, "EUR")
    assert eur_tag != "Seiryu Tag" and TABLES.key_item_jp_in_eur(22)
    assert TABLES.key_item_jp_in_eur(45)          # Recovery CD 3
    assert not TABLES.key_item_jp_in_eur(32)      # World Champ is localized on EUR
    assert TABLES.key_item_name(32, "EUR") == "Koc Trophy"
    assert TABLES.key_item_name(33, "EUR") == "Platinum Card"
    assert TABLES.key_item_name(16, "EUR") == "Sun Trophy"      # same both
    assert sum(TABLES.key_item_regions_differ(i) for i in range(48)) == 11
    assert sum(TABLES.key_item_jp_in_eur(i) for i in range(48)) == 9


# ---- key items (CONFIRMED 2026-09-02 vs player's Important screen) ------
def test_key_item_offsets_map_to_expected_bytes(usa):
    # Block A starts at 0x0380; Monmon DDNA at main-array slot 317 (0x04E4);
    # Block B starts at 0x0507.
    assert key_item_offset(0) == 0x0380
    assert key_item_offset(38) == 0x03A6
    assert key_item_offset(39) == 0x04E4
    assert key_item_offset(40) == 0x0507
    assert key_item_offset(47) == 0x050E
    with pytest.raises(SaveError):
        key_item_offset(48)


def test_key_item_read_and_set_round_trip(usa):
    n0 = usa.key_item_count(0)  # Tree Boots
    usa.set_key_item(0, 0 if n0 else 1)
    again = DMW3Save(usa.to_bytes())
    assert again.key_item_count(0) == (0 if n0 else 1)
    assert again.checksum_valid


def test_key_item_bounds_enforced(usa):
    with pytest.raises(SaveError):
        usa.key_item_count(KEY_ITEM_COUNT)
    with pytest.raises(SaveError):
        usa.set_key_item(0, 2)
    with pytest.raises(SaveError):
        usa.set_key_item(-1, 1)


def test_set_all_key_items(usa):
    usa.set_all_key_items(1)
    for i in range(KEY_ITEM_COUNT):
        assert usa.key_item_count(i) == 1
    usa.set_all_key_items(0)
    for i in range(KEY_ITEM_COUNT):
        assert usa.key_item_count(i) == 0
    assert DMW3Save(usa.to_bytes()).checksum_valid


# ---- card packs (CONFIRMED 2026-09-02 vs player's item tab) -------------
def test_pack_slots_write_through_item_array(usa):
    # Packs are bytes of the main item-qty array; writing a pack count must
    # change exactly that byte and keep both checksums valid.
    before = bytes(usa.to_bytes())
    usa.set_item_qty(TABLES.pack_save_slot(0), 42)  # Booster 01a @ slot 48
    usa.set_item_qty(TABLES.pack_save_slot(34), 7)  # R-Booster 05 @ slot 351
    out = usa.to_bytes()
    assert out[ITEM_BASE + 48] == 42
    assert out[ITEM_BASE + 351] == 7
    assert ck.verify_header(out)
    assert ck.verify_chunk2(out)
    # only the two intended bytes changed inside the item array region
    changed = [
        i for i in range(ITEM_BASE, ITEM_BASE + 352)
        if out[i] != before[i]
    ]
    assert changed == [ITEM_BASE + 48, ITEM_BASE + 351]


# ---- per-Digimon stats (CONFIRMED 2026-09-02 vs live anchors) -----------
def test_digimon_stat_blocks_match_roster(usa):
    # record 0 must be Kotemon; fresh sample cards hold maxed partners
    # (Lv99/9999/999 on the user's save — check structure is coherent).
    for i in range(DIGI_STAT_COUNT):
        name = usa.digimon_name(i)
        st = usa.digimon_stats(i)
        assert st["level"] >= 1
        assert st["hp"] == st["hp_max"]  # pairs written together
        assert st["mp"] == st["mp_max"]
        assert len(st["stats"]) == 13


def test_digimon_stat_offsets_match_live_anchors(usa):
    # The anchors from the player's maxed EUR card: HP/MP u16 at +0x40/+0x44,
    # EXP u32 at +0x38, level u16 at +0x3C, 13 stats at +0x48.
    base = DIGI_STAT_BASE
    assert DIGI_STAT_BASE == 0x0A48
    assert DIGI_STAT_STRIDE == 0x3DC
    assert D_EXP == 0x38 and D_LEVEL == 0x3C and D_HP == 0x40 and D_STATS == 0x48


def test_digimon_edit_round_trip_and_checksums(usa):
    before = bytes(usa.to_bytes())
    usa.set_digimon_level(0, 50)
    usa.set_digimon_exp(0, 123456)
    usa.set_digimon_hp(0, 4321)
    usa.set_digimon_mp(0, 5555)
    usa.set_digimon_stat(0, 0, 123)   # Strength
    usa.set_digimon_stat(0, 12, 321)  # Dark
    out = usa.to_bytes()
    assert ck.verify_header(out) and ck.verify_chunk2(out)
    again = DMW3Save(out)
    st = again.digimon_stats(0)
    assert st["level"] == 50
    assert st["exp"] == 123456
    assert st["hp"] == 4321 and st["hp_max"] == 4321
    assert st["mp"] == 5555 and st["mp_max"] == 5555
    assert st["stats"][0] == 123 and st["stats"][12] == 321
    # only intended bytes changed inside the stat record
    changed = [i for i in range(DIGI_STAT_BASE, DIGI_STAT_BASE + DIGI_STAT_STRIDE)
               if out[i] != before[i]]
    assert set(changed) == {
        DIGI_STAT_BASE + 0x38, DIGI_STAT_BASE + 0x39,  # exp u32 (123456 needs 3 bytes)
        DIGI_STAT_BASE + 0x3A,                          # +0x3B already 0 on USA sample
        DIGI_STAT_BASE + 0x3C,                          # level u16 (high byte +0x3D stays 0)
        DIGI_STAT_BASE + 0x40, DIGI_STAT_BASE + 0x41,  # hp u16
        DIGI_STAT_BASE + 0x42, DIGI_STAT_BASE + 0x43,
        DIGI_STAT_BASE + 0x44, DIGI_STAT_BASE + 0x45,  # mp u16
        DIGI_STAT_BASE + 0x46, DIGI_STAT_BASE + 0x47,
        DIGI_STAT_BASE + 0x48, DIGI_STAT_BASE + 0x49,  # str
        DIGI_STAT_BASE + 0x60, DIGI_STAT_BASE + 0x61,  # dark
    }


def test_digimon_edit_bounds_enforced(usa):
    with pytest.raises(SaveError):
        usa.set_digimon_level(0, 100)
    with pytest.raises(SaveError):
        usa.set_digimon_level(0, 0)
    with pytest.raises(SaveError):
        usa.set_digimon_exp(0, DIGI_MAX_EXP + 1)
    with pytest.raises(SaveError):
        usa.set_digimon_hp(0, DIGI_MAX_HP + 1)
    with pytest.raises(SaveError):
        usa.set_digimon_stat(0, 13, 5)
    with pytest.raises(SaveError):
        usa.set_digimon_stat(0, 0, DIGI_MAX_STAT + 1)
    with pytest.raises(SaveError):
        usa.digimon_stats(8)
    with pytest.raises(SaveError):
        usa.set_digimon_level(-1, 50)


def test_digimon_maxed_helper(usa):
    usa.set_digimon_maxed(3)
    st = usa.digimon_stats(3)
    assert st["level"] == 99 and st["exp"] == 999999
    assert st["hp"] == 9999 and st["mp"] == 9999
    assert all(v == 999 for v in st["stats"])
    assert DMW3Save(usa.to_bytes()).checksum_valid


# ---- edits ---------------------------------------------------------------
def test_money_round_trips(usa):
    usa.set_money(0, 12345)
    assert DMW3Save(usa.to_bytes()).slots[0].money == 12345


def test_money_bounds_enforced(usa):
    with pytest.raises(SaveError):
        usa.set_money(0, MONEY_MAX + 1)
    with pytest.raises(SaveError):
        usa.set_money(0, -1)


def test_digimon_injection_round_trips(usa):
    """Inject Guilmon (USA party id 6) at level 99 into slot 0, position 0.

    Party slots accept ONLY the 8 base rookies. USA uses decomp ids 1..8,
    EUR uses +2 (3..10); writing evolved/enemy ids stalls the game on load
    (confirmed by the user's EUR card edit).
    """
    usa.set_party_member(0, 0, 6, 99)
    again = DMW3Save(usa.to_bytes())
    assert again.slots[0].party[0] == (6, 99)
    assert again.slots[0].party_text.startswith("Guilmon")
    assert again.checksum_valid


def test_party_rejects_evolved_digimon_ids(usa):
    """Writing an evolved/enemy form into the party slot must be refused."""
    omnimon = next(i for i, n in TABLES.digimon.items() if n == "Omnimon")
    assert omnimon > 10
    with pytest.raises(SaveError, match="base rookies"):
        usa.set_party_member(0, 0, omnimon, 99)
    with pytest.raises(SaveError, match="base rookies"):
        usa.set_partner(0, omnimon)
    # 0 (empty) is never a valid party member id, and USA ids are 1..8, so
    # id 0 and id 9+ must be refused on a USA save.
    with pytest.raises(SaveError):
        usa.set_party_member(0, 0, 0, 99)
    with pytest.raises(SaveError):
        usa.set_partner(0, 9)
    # the failed writes must not have touched the buffer
    assert usa.slots[0].party[0][0] != omnimon


def test_eur_rejects_decomp_ids_1_and_2(eur):
    """EUR party space is 3..10 — ids 1-2 are invalid there (user-proven)."""
    with pytest.raises(SaveError, match="base rookies"):
        eur.set_party_member(0, 0, 1, 99)
    with pytest.raises(SaveError, match="base rookies"):
        eur.set_partner(0, 2)


def test_level_bounds_enforced(usa):
    with pytest.raises(SaveError):
        usa.set_party_member(0, 0, 6, 100)
    with pytest.raises(SaveError):
        usa.set_party_member(0, 0, 6, 0)


def test_unknown_digimon_id_rejected(usa):
    with pytest.raises(SaveError, match="base rookies"):
        usa.set_party_member(0, 0, 9999, 50)


def test_partner_and_play_time_round_trip(usa):
    usa.set_partner(0, 2)          # Kumamon (USA party id 2)
    usa.set_play_time(0, 12, 34, 56)
    again = DMW3Save(usa.to_bytes()).slots[0]
    assert again.partner_name == "Kumamon"
    assert again.play_time == (12, 34, 56)


def test_bad_play_time_rejected(usa):
    with pytest.raises(SaveError):
        usa.set_play_time(0, 1, 60, 0)


# ---- safety --------------------------------------------------------------
def test_writes_to_unidentified_regions_are_refused(usa):
    for offset in (0x2900, 0x3000, 0x5000, 0x6FFF):
        with pytest.raises(SaveError, match="not understood"):
            usa.set_byte(offset, 0x00)


def test_serialization_repairs_checksum_after_edit(usa):
    usa.set_money(0, 1)
    out = bytearray(usa.to_bytes())
    assert ck.verify_header(out)


def test_untouched_save_serializes_byte_identical():
    original = (ROOT / "samples" / "USA_save.bin").read_bytes()
    assert DMW3Save(original).to_bytes() == original


def test_edits_only_touch_intended_bytes():
    original = (ROOT / "samples" / "USA_save.bin").read_bytes()
    save = DMW3Save(original)
    save.set_money(1, 555)
    out = save.to_bytes()
    changed = {i for i in range(len(original)) if original[i] != out[i]}
    money_at = SLOT_OFFSETS[1] + 0x20
    allowed = set(range(money_at, money_at + 4)) | {0x0200, 0x0201}
    assert changed <= allowed, [hex(x) for x in sorted(changed - allowed)]


# ---- digivolution DV levels (CONFIRMED 2026-09-02 live probe) ------------
def test_digimon_dv_layout_offsets():
    """The DV level u16 lives at header +0x72 and each data slot +18."""
    assert D_DV_HEADER == 0x72
    assert D_DV_SLOTS == 0x74
    assert D_DV_SLOT_STRIDE == 20
    assert D_DV_SLOT_LEVEL == 18
    assert D_DV_COUNT == 43
    assert D_DV_MAX == 99


def test_digimon_dv_read_returns_43_slots(usa):
    dv = usa.digimon_dv(0)
    assert set(dv) == {"header", "slots", "markers"}
    assert isinstance(dv["header"], int)
    assert len(dv["slots"]) == D_DV_COUNT
    assert all(0 <= v <= 99 for v in dv["slots"])
    assert len(dv["markers"]) == D_DV_COUNT
    assert all(isinstance(m, int) for m in dv["markers"])


def test_set_digimon_dv_header_writes_probe_offset(usa):
    rec = DIGI_STAT_BASE + 0 * DIGI_STAT_STRIDE
    before = usa._buf[rec + D_DV_HEADER:rec + D_DV_HEADER + 2]
    usa.set_digimon_dv_header(0, 42)
    after = usa._buf[rec + D_DV_HEADER:rec + D_DV_HEADER + 2]
    assert before != after and after == b"\x2a\x00"
    out = usa.to_bytes()
    assert ck.verify_header(bytearray(out))


def test_set_digimon_dv_slot_writes_slot18(usa):
    rec = DIGI_STAT_BASE + 3 * DIGI_STAT_STRIDE  # Agumon
    slot = 5
    off = rec + D_DV_SLOTS + slot * D_DV_SLOT_STRIDE + D_DV_SLOT_LEVEL
    usa.set_digimon_dv_slot(3, slot, 77)
    assert usa._buf[off:off + 2] == b"\x4d\x00"
    assert usa.digimon_dv(3)["slots"][slot] == 77
    out = usa.to_bytes()
    assert ck.verify_all(bytearray(out))


def test_digimon_dv_range_checks(usa):
    with pytest.raises(SaveError):
        usa.set_digimon_dv_slot(3, -1, 50)
    with pytest.raises(SaveError):
        usa.set_digimon_dv_slot(3, 43, 50)
    with pytest.raises(SaveError):
        usa.set_digimon_dv_slot(3, 0, 100)
    with pytest.raises(SaveError):
        usa.set_digimon_dv_header(0, 0)   # header must stay >= 1


def test_dv_orders_tables_match_readbacks():
    """digivolve_orders.json slot lists match the user's in-game reads
    (probe tags 1..43 displayed the exact names in slot order)."""
    h, slots = TABLES.dv_order("Agumon")
    assert h == "Greymon"
    assert slots[:3] == ["MetalGreymon", "WarGreymon", "Dinohumon"]
    assert slots[-1] == "GranKuwagamon" and len(slots) == 30
    h, slots = TABLES.dv_order("Patamon")
    assert h == "Angemon"
    assert slots == ["MagnaAngemon", "Seraphimon", "Hookmon", "Greymon",
                     "Stingmon", "Angewomon", "Digitamamon"]
    assert TABLES.dv_order("NoSuchDigimon") == ("", [])


# ---- DV form markers @ slot+16..17 (the "earned" identity bytes) ---------
# Measured 2026-09-02 from the EUR maxed card (captures/after_ITEM.mcr and the
# identical-lineage samples/EUR_raw.mcr): every DV data slot has a constant
# per-form 2-byte marker at +16..17 (level u16 is at +18..19). Empty slots
# (never earned) carry marker 0. Markers are unique per evolved form and
# card-independent; probe 2 proved level alone does NOT earn a form — the
# marker is what the game reads as the form's identity/obtained state.
# The canonical table lives in save.py (DV_FORM_MARKERS, incl. Diaboromon=151
# measured from the USA genuine card).


def test_dv_markers_present_in_eur_sample(eur):
    """EUR maxed sample: the marker u16 at each earned slot's +16..17 matches
    the digivolve_orders.json name for that slot."""
    seen = {}
    for ri in range(8):
        roster = DIGI_ROSTER_NAMES[ri]
        _, slot_names = TABLES.dv_order(roster)
        dv = eur.digimon_dv(ri)
        # digimon_dv returns levels; for markers we need the raw slot bytes.
        rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
        for k, name in enumerate(slot_names):
            if dv["slots"][k] <= 0:
                continue
            off = rec + D_DV_SLOTS + k * D_DV_SLOT_STRIDE + 16
            marker = int.from_bytes(eur._buf[off:off + 2], "little")
            assert marker == DV_FORM_MARKERS[name], (roster, k, name, marker)
            seen[name] = marker
    assert len(seen) == 43  # every evolved form except Diaboromon is on EUR


def test_dv_marker_table_is_complete_and_unique():
    """All 44 evolved forms have a marker; no two forms share one."""
    from dmw3editor.ui.collections import EVOLVED_FORMS_44  # canonical order

    assert set(EVOLVED_FORMS_44) == set(DV_FORM_MARKERS)
    assert len(set(DV_FORM_MARKERS.values())) == len(DV_FORM_MARKERS) == 44


def test_earn_digimon_dv_writes_marker_and_level(eur):
    """Force-earning writes the form's marker into the next empty slot and
    sets the DV level — CONFIRMED in-game 2026-09-02 (Seraphimon 42 and
    Rosemon 7 appeared on Agumon's DV screen). Since 2026-09-03 it also
    writes the form's display content into the FOLLOWING slot (V5 proof:
    that is where the DV screen reads a row's techniques)."""
    ri = 3  # Agumon on the EUR card (has empty slots)
    rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
    free = None
    dv = eur.digimon_dv(ri)
    for k in range(D_DV_COUNT):
        if dv["markers"][k] == 0:
            free = k
            break
    assert free is not None, "expected at least one empty DV slot on EUR Agumon"
    slot_used = eur.earn_digimon_dv(ri, "Seraphimon", 42)
    assert slot_used == free
    off = rec + D_DV_SLOTS + free * D_DV_SLOT_STRIDE
    assert eur._buf[off + 16:off + 18] == b"\xd6\x00"      # marker 214
    assert eur._buf[off + 18:off + 20] == b"\x2a\x00"      # level 42
    dv2 = eur.digimon_dv(ri)
    assert dv2["markers"][free] == 214 and dv2["slots"][free] == 42
    out = eur.to_bytes()
    assert ck.verify_all(bytearray(out))
    # earning into a full table is refused (USA genuine card: all 43 full)
    usa_full = load("USA_save.bin")
    with pytest.raises(SaveError, match="all 43 DV slots"):
        usa_full.earn_digimon_dv(0, "Rosemon", 5)
    with pytest.raises(SaveError):
        eur.earn_digimon_dv(ri, "BadName", 5)
    with pytest.raises(SaveError):
        eur.earn_digimon_dv(ri, "Rosemon", 0)
    with pytest.raises(SaveError):
        eur.earn_digimon_dv(7, "Rosemon", 5, slot=43)


def test_earn_writes_display_content_into_next_slot(eur):
    """Earning writes the row's tech content into the FOLLOWING slot's content
    field (slot+1 .. +4..+15) — the DV screen reads row k's techniques from
    slot k+1's content record. Devimon marker 6, level 99 => its full profile
    techs; slot30 (first free on EUR Agumon) => content lands in slot31."""
    ri = 3
    slot_used = eur.earn_digimon_dv(ri, "Devimon", 99)
    rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
    # content for the just-earned slot is stored at slot+1's content field
    nxt = rec + D_DV_SLOTS + (slot_used + 1) * D_DV_SLOT_STRIDE + D_DV_SLOT_CONTENT
    got = bytes(eur._buf[nxt:nxt + D_DV_SLOT_CONTENT_LEN])
    want = dv_tech_content(DV_FORM_MARKERS["Devimon"], 99)
    assert got == want
    assert any(got), "display content must not be all-zero at level 99"
    out = eur.to_bytes()
    assert ck.verify_all(bytearray(out))


def test_set_dv_level_syncs_following_slot_content(eur):
    """Raising an earned row's DV level must refresh the row's display content
    in the following slot (this is the 'rows 21-29 showed no techs after the
    all-99 pass' bug: level bytes moved but content stayed zero)."""
    ri = 3
    # EUR Agumon slot 22 (Armormon, marker 390) was earned at DV1 with zero content
    dv = eur.digimon_dv(ri)
    k22 = next(k for k in range(D_DV_COUNT) if dv["markers"][k] == 390)
    rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
    nxt = rec + D_DV_SLOTS + (k22 + 1) * D_DV_SLOT_STRIDE + D_DV_SLOT_CONTENT
    eur.set_digimon_dv_slot(ri, k22, 99)
    got = bytes(eur._buf[nxt:nxt + D_DV_SLOT_CONTENT_LEN])
    want = dv_tech_content(390, 99)
    assert got == want
    assert any(got)
    assert ck.verify_all(bytearray(eur.to_bytes()))


def test_sync_digimon_dv_contents_fills_all_earned_rows(eur):
    """sync_digimon_dv_contents rebuilds every earned row's display content so
    rows earned naturally at DV1 (empty content) gain their moves at the DV
    level the save holds — the editor-side equivalent of V5's card fix."""
    ri = 3
    eur.sync_digimon_dv_contents(ri)
    rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
    dv = eur.digimon_dv(ri)
    checked = 0
    for k in range(D_DV_COUNT):
        marker = dv["markers"][k]
        level = dv["slots"][k]
        if not marker or not level:
            continue
        if k < D_DV_COUNT - 1:
            nxt = rec + D_DV_SLOTS + (k + 1) * D_DV_SLOT_STRIDE + D_DV_SLOT_CONTENT
        else:
            nxt = rec + D_DV_SLOT_CONTENT_PHANTOM
        got = bytes(eur._buf[nxt:nxt + D_DV_SLOT_CONTENT_LEN])
        want = dv_tech_content(marker, level)
        assert got == want, f"slot {k} content mismatch"
        if level >= 50:
            assert any(got), f"slot {k} lv{level} should show techs"
        checked += 1
    assert checked >= 20
    assert ck.verify_all(bytearray(eur.to_bytes()))


def test_dv_tech_content_level_scaling():
    """dv_tech_content zeroes tech pairs whose learn threshold exceeds level.

    Natural lv1 rows keep the record tail (e.g. 7f96) but carry no tech pairs;
    the donor seed reproduces that: pairs zeroed, tail preserved."""
    full = dv_tech_content(DV_FORM_MARKERS["Devimon"], 99)
    assert any(full)
    lo = dv_tech_content(DV_FORM_MARKERS["Devimon"], 1)
    # Devimon's first tech learns at DV 10 -> no tech pairs at DV1
    assert not any(lo[:10])
    mid = dv_tech_content(DV_FORM_MARKERS["Devimon"], 30)
    # learn thresholds for Devimon: 10/20/35/55 -> at 30 only first two pairs
    pairs_nonzero = sum(1 for i in range(0, 10, 2) if mid[i] != 0)
    assert 0 < pairs_nonzero < 5


def test_dv_empty_slots_have_zero_marker(usa):
    """USA genuine card earned order differs from EUR; its marker bytes should
    still be nonzero wherever DV level > 0, zero wherever level == 0."""
    for ri in range(8):
        dv = usa.digimon_dv(ri)
        rec = DIGI_STAT_BASE + ri * DIGI_STAT_STRIDE
        for k in range(D_DV_COUNT):
            off = rec + D_DV_SLOTS + k * D_DV_SLOT_STRIDE + 16
            marker = int.from_bytes(usa._buf[off:off + 2], "little")
            if dv["slots"][k] > 0:
                assert marker != 0
            else:
                assert marker == 0
