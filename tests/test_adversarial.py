"""Adversarial tests: malformed input, boundaries, and fuzzed round-trips.

The point of this file is to BREAK the editor, not to confirm it works. Anything
that reaches a user's memory card has to survive garbage input without throwing
an unhandled struct.error / IndexError and without silently writing wrong bytes.
"""

import pathlib
import random
import struct
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import checksum as ck
from dmw3editor.core import memcard as mc
from dmw3editor.core.save import (
    DATA_SECTION_OFFSETS,
    DIGI_STAT_BASE_REL,
    DIGI_STAT_STRIDE,
    DMW3Save,
    D_LEVEL,
    D_UNLOCK,
    GS_PARTY,
    LEVEL_MAX,
    MONEY_MAX,
    PARTY_SIZE,
    SLOT_OFFSETS,
    TABLES,
    SaveError,
    party_index_for_id,
    party_min_for_region,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
USA = ROOT / "samples" / "USA_save.bin"
EUR = ROOT / "samples" / "EUR_save.bin"

# Exceptions we consider "handled". A bare struct.error or IndexError escaping
# the library is a bug, so those are deliberately NOT in this tuple.
HANDLED = (SaveError, ValueError, OSError)


def usa():
    return DMW3Save(USA.read_bytes())


# --------------------------------------------------------------------------
# malformed payloads
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\x00",
        bytes(1024),
        bytes(32767),
        bytes(32769),
        b"\xff" * 32768,
        bytes(131072),
    ],
    ids=["empty", "one-byte", "short", "off-by-one-small", "off-by-one-big",
         "all-ff", "whole-card"],
)
def test_malformed_payloads_raise_cleanly(payload):
    with pytest.raises(HANDLED):
        DMW3Save(payload)


def test_payload_with_right_size_but_no_magic_is_rejected():
    buf = bytearray(32768)
    buf[0x0204:0x0208] = b"XXXX"
    with pytest.raises(SaveError, match="not a Digimon World 3 save"):
        DMW3Save(buf)


def test_truncated_magic_is_rejected():
    buf = bytearray(USA.read_bytes())
    buf[0x0207] = 0x00  # 'DMW3' -> 'DMW\0'
    with pytest.raises(SaveError):
        DMW3Save(buf)


# --------------------------------------------------------------------------
# malformed containers
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"MC",
        bytes(64),
        bytes(131071),
        b"\xff" * 131072,
        b"\x00" * 3903,          # truncated .gme header
    ],
    ids=["empty", "magic-only", "tiny", "short-card", "all-ff-card",
         "truncated-gme"],
)
def test_malformed_containers_never_crash_uncaught(tmp_path, data):
    path = tmp_path / "card.mcr"
    path.write_bytes(data)
    try:
        card = mc.MemoryCard.load(str(path))
    except HANDLED:
        return  # rejected at load: fine
    # Or it loads but must report no DMW3 save rather than exploding.
    try:
        assert card.find_dmw3_save() is None
    except HANDLED:
        pass


def test_blank_but_valid_card_reports_no_save(tmp_path):
    buf = bytearray(131072)
    buf[0:2] = b"MC"
    for frame in range(1, 16):
        buf[frame * 128] = 0xA0  # every slot free
    path = tmp_path / "blank.mcr"
    path.write_bytes(buf)
    card = mc.MemoryCard.load(str(path))
    assert card.find_dmw3_save() is None


def test_directory_claiming_a_runaway_block_chain_is_survivable(tmp_path):
    """A corrupt 'next block' pointer must not hang or read out of bounds."""
    buf = bytearray(131072)
    buf[0:2] = b"MC"
    entry = 1 * 128
    struct.pack_into("<I", buf, entry, 0x51)
    struct.pack_into("<I", buf, entry + 4, 32768)
    struct.pack_into("<H", buf, entry + 8, 9999)  # nonexistent next block
    buf[entry + 10:entry + 30] = b"BASLUS-01436DMW3-USA"
    path = tmp_path / "corrupt.mcr"
    path.write_bytes(buf)

    card = mc.MemoryCard.load(str(path))
    try:
        loc = card.find_dmw3_save()
        if loc is not None:
            payload = card.extract_payload(loc)
            assert len(payload) <= 32768
    except HANDLED:
        pass


def test_self_referential_block_chain_terminates(tmp_path):
    """A chain that points at itself must not loop forever."""
    buf = bytearray(131072)
    buf[0:2] = b"MC"
    entry = 1 * 128
    struct.pack_into("<I", buf, entry, 0x51)
    struct.pack_into("<I", buf, entry + 4, 32768)
    struct.pack_into("<H", buf, entry + 8, 1)  # points to itself
    buf[entry + 10:entry + 30] = b"BASLUS-01436DMW3-USA"
    path = tmp_path / "loop.mcr"
    path.write_bytes(buf)

    card = mc.MemoryCard.load(str(path))
    try:
        loc = card.find_dmw3_save()
        if loc is not None:
            assert len(card.extract_payload(loc)) <= 32768
    except HANDLED:
        pass


# --------------------------------------------------------------------------
# boundary values
# --------------------------------------------------------------------------
@pytest.mark.parametrize("value", [-1, MONEY_MAX + 1, 1 << 32, 1 << 64])
def test_out_of_range_money_rejected(value):
    with pytest.raises(SaveError):
        usa().set_money(0, value)


@pytest.mark.parametrize("value", [0, 1, MONEY_MAX])
def test_in_range_money_accepted(value):
    s = usa()
    s.set_money(0, value)
    assert DMW3Save(s.to_bytes()).slots[0].money == value


@pytest.mark.parametrize("level", [-1, 0, LEVEL_MAX + 1, 255, 1 << 20])
def test_out_of_range_level_rejected(level):
    with pytest.raises(SaveError):
        usa().set_party_member(0, 0, 6, level)


@pytest.mark.parametrize("did", [-1, 251, 70000])
def test_out_of_range_digimon_id_rejected(did):
    with pytest.raises(SaveError):
        usa().set_party_member(0, 0, did, 50)


@pytest.mark.parametrize("pos", [-1, PARTY_SIZE, 99])
def test_bad_party_position_rejected(pos):
    with pytest.raises(SaveError):
        usa().set_party_member(0, pos, 6, 50)


@pytest.mark.parametrize(
    "h,m,s",
    [(0, 60, 0), (0, 0, 60), (-1, 0, 0), (0, -1, 0), (1000, 0, 0)],
)
def test_bad_play_time_rejected(h, m, s):
    with pytest.raises(SaveError):
        usa().set_play_time(0, h, m, s)


def test_boundary_play_time_accepted():
    s = usa()
    s.set_play_time(0, 0, 59, 59)
    assert DMW3Save(s.to_bytes()).slots[0].play_time == (0, 59, 59)


@pytest.mark.parametrize("value", [-1, 256, 1000])
def test_bad_byte_value_rejected(value):
    with pytest.raises(SaveError):
        usa().set_byte(0x0210, value)


@pytest.mark.parametrize("offset", [-1, 32768, 1 << 30])
def test_out_of_range_byte_offset_rejected(offset):
    with pytest.raises(SaveError):
        usa().set_byte(offset, 0)


def test_bad_slot_index_does_not_write_silently():
    """An out-of-range slot must raise, never wrap around and corrupt another."""
    for bad in (-1, len(SLOT_OFFSETS), 99):
        s = usa()
        before = s.to_bytes()
        with pytest.raises((SaveError, IndexError)):
            s.set_money(bad, 1234)
        # Even if it raised, nothing may have been written.
        assert s.to_bytes() == before


# --------------------------------------------------------------------------
# invariants under fuzzing
# --------------------------------------------------------------------------
def test_fuzzed_edit_sequences_preserve_every_invariant():
    original = USA.read_bytes()
    rng = random.Random(0xD1123400)
    ids = sorted(TABLES.digimon)

    for _ in range(300):
        save = DMW3Save(original)
        expected = {}
        for _ in range(rng.randint(1, 6)):
            slot = rng.randrange(len(SLOT_OFFSETS))
            choice = rng.randrange(4)
            if choice == 0:
                v = rng.randrange(0, MONEY_MAX + 1)
                save.set_money(slot, v)
                expected[("money", slot)] = v
            elif choice == 1:
                pos = rng.randrange(PARTY_SIZE)
                # Party slots accept only the 8 base rookies, ids 3..10 on
                # BOTH regions (id = index + 3; the space is region-independent,
                # see the party-space note in save.py).
                pmin = party_min_for_region(save.region_guess)
                did = rng.randrange(pmin, pmin + 8)
                lv = rng.randint(1, LEVEL_MAX)
                save.set_party_member(slot, pos, did, lv)
                expected[("party", slot, pos)] = (did, lv)
            elif choice == 2:
                pmin = party_min_for_region(save.region_guess)
                did = rng.randrange(pmin, pmin + 8)
                save.set_partner(slot, did)
                expected[("partner", slot)] = did
            else:
                h, m, s = rng.randint(0, 999), rng.randint(0, 59), rng.randint(0, 59)
                save.set_play_time(slot, h, m, s)
                expected[("time", slot)] = (h, m, s)

        out = save.to_bytes()
        assert len(out) == 32768
        assert ck.verify_header(bytearray(out))

        again = DMW3Save(out)
        for key, want in expected.items():
            if key[0] == "money":
                assert again.slots[key[1]].money == want
            elif key[0] == "party":
                assert again.slots[key[1]].party[key[2]] == want
            elif key[0] == "partner":
                assert again.slots[key[1]].partner_id == want
            else:
                assert again.slots[key[1]].play_time == want


def test_edits_never_touch_bytes_outside_their_field():
    original = USA.read_bytes()
    rng = random.Random(7)
    checksum_bytes = {0x0200, 0x0201}

    for _ in range(120):
        save = DMW3Save(original)
        slot = rng.randrange(len(SLOT_OFFSETS))
        base = SLOT_OFFSETS[slot]
        field, size = rng.choice([(0x20, 4), (0x18, 4), (0x30, 4), (0x3C, 2)])
        party_member = False
        if size == 4 and field in (0x18, 0x30):
            party_member = field == 0x30
            save_fn = (
                (lambda: save.set_partner(slot, 6))
                if field == 0x18
                else (lambda: save.set_party_member(slot, 0, 6, 98))
            )
        elif field == 0x20:
            save_fn = lambda: save.set_money(slot, 4242)  # noqa: E731
        else:
            party_member = True
            save_fn = lambda: save.set_party_member(slot, 0, 6, 55)  # noqa: E731
        save_fn()

        out = save.to_bytes()
        changed = {i for i in range(len(original)) if original[i] != out[i]}
        # set_party_member writes the summary id (4B) + level (2B) AND, when the
        # slot's data section is writable, the authoritative data-section party
        # (index 4B), the partner's unlocked id (4B) and its STAT_LEVEL (2B).
        allowed = (
            set(range(base + 0x30, base + 0x34))
            | set(range(base + 0x3C, base + 0x3E))
            | set(range(base + field, base + field + size))
            | checksum_bytes
        )
        if party_member and save.party_data_written(slot):
            ds = DATA_SECTION_OFFSETS[slot]
            idx = party_index_for_id(6, save.region_guess)
            party_off = ds + GS_PARTY
            partner_off = ds + DIGI_STAT_BASE_REL + idx * DIGI_STAT_STRIDE
            allowed |= set(range(party_off, party_off + 4))
            allowed |= set(range(partner_off + D_UNLOCK, partner_off + D_UNLOCK + 4))
            allowed |= set(range(partner_off + D_LEVEL, partner_off + D_LEVEL + 2))
            allowed.add(ds)  # data-section checksum byte (chunk 2)
        assert changed <= allowed, [hex(x) for x in sorted(changed - allowed)]


def test_no_op_serialization_is_byte_identical():
    for path in (USA, EUR):
        raw = path.read_bytes()
        assert DMW3Save(raw).to_bytes() == raw


def test_applying_the_same_edit_twice_is_idempotent():
    for path in (USA, EUR):
        raw = path.read_bytes()
        once = DMW3Save(raw)
        once.set_money(0, 5555)
        first = once.to_bytes()

        twice = DMW3Save(first)
        twice.set_money(0, 5555)
        assert twice.to_bytes() == first


def test_unidentified_regions_stay_refused():
    s = usa()
    for offset in (0x2900, 0x2901, 0x4000, 0x5000, 0x76FF):
        with pytest.raises(SaveError, match="not understood"):
            s.set_byte(offset, 0xAB)


def test_edits_to_one_slot_never_disturb_another():
    original = USA.read_bytes()
    for target in range(len(SLOT_OFFSETS)):
        save = DMW3Save(original)
        untouched = [
            (i, DMW3Save(original).slots[i].money,
             DMW3Save(original).slots[i].party)
            for i in range(len(SLOT_OFFSETS)) if i != target
        ]
        save.set_money(target, 4321)
        save.set_party_member(target, 0, 6, 77)  # Guilmon (USA party id 6)
        after = DMW3Save(save.to_bytes())
        for i, money, party in untouched:
            assert after.slots[i].money == money
            assert after.slots[i].party == party
