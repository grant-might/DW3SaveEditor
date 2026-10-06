import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from dmw3editor.core.model import (
    DMW3Save, RECORD_BASE, RECORD_SIZE, BACKUP_BASES, PARTY_STRIDE,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIG = bytes([0x13, 0x40, 0x2B, 0x01, 0x01, 0x0D, 0x0D, 0x00])


def load(name):
    return DMW3Save.from_bytes((ROOT / "samples" / name).read_bytes())


def test_primary_record_is_tagged_on_both_cards():
    assert load("USA_save.bin").primary.occupied
    assert load("EUR_save.bin").primary.occupied


def test_dmw3_tag_occurs_exactly_once_in_payload():
    """The evidence that killed the three-slot model. Guard it with a test."""
    for name in ("USA_save.bin", "EUR_save.bin"):
        raw = (ROOT / "samples" / name).read_bytes()
        assert raw.count(b"DMW3") == 1, name
        assert raw.find(b"DMW3") == RECORD_BASE + 4, name


def test_usa_has_backup_copies_eur_does_not():
    assert load("USA_save.bin").backup_copies_present() is True
    assert load("EUR_save.bin").backup_copies_present() is False


def test_backup_copies_are_near_identical_to_each_other():
    """B vs C differ in only 6 bytes; both differ from primary by ~155."""
    raw = (ROOT / "samples" / "USA_save.bin").read_bytes()
    a = raw[RECORD_BASE:RECORD_BASE + RECORD_SIZE]
    b = raw[BACKUP_BASES[0]:BACKUP_BASES[0] + RECORD_SIZE]
    c = raw[BACKUP_BASES[1]:BACKUP_BASES[1] + RECORD_SIZE]
    d = lambda x, y: sum(1 for i, j in zip(x, y) if i != j)
    assert d(b, c) < 20
    assert 100 < d(a, b) < 300
    assert 100 < d(a, c) < 300


def test_party_is_three_records_of_68_bytes_with_signature():
    party = load("USA_save.bin").primary.party
    assert len(party) == 3
    for m in party:
        assert len(m.raw) == PARTY_STRIDE
        assert bytes(m.raw[:8]) == SIG, m.index


def test_payload_roundtrip_is_byte_exact():
    raw = (ROOT / "samples" / "USA_save.bin").read_bytes()
    assert DMW3Save.from_bytes(raw).to_bytes() == raw


def test_edit_then_revert_is_byte_exact():
    raw = (ROOT / "samples" / "USA_save.bin").read_bytes()
    s = DMW3Save.from_bytes(raw)
    rec = s.primary
    m = rec.party[0]
    orig = m.u32(0x20)
    m.set_u32(0x20, 4242)
    rec.write_party_member(m)
    s.write_record(rec)
    assert s.primary.party[0].u32(0x20) == 4242
    assert s.to_bytes() != raw
    m.set_u32(0x20, orig)
    rec.write_party_member(m)
    s.write_record(rec)
    assert s.to_bytes() == raw


def test_near_max_u32_at_party_plus_0x20():
    """9,999,951 - just under a 9,999,999 decimal cap, so a counter (EXP-like),
    not a bitfield. All three party records share the same value."""
    party = load("USA_save.bin").primary.party
    assert [m.u32(0x20) for m in party] == [9999951] * 3


def test_mirror_to_backups_is_explicit_and_reports_count():
    s = load("USA_save.bin")
    assert s.mirror_primary_to_backups() == 2
    a = s.payload[RECORD_BASE:RECORD_BASE + RECORD_SIZE]
    for base in BACKUP_BASES:
        assert s.payload[base:base + RECORD_SIZE] == a
