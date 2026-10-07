"""Controlled-diff tests.

These prove the diff tool can isolate a SINGLE in-game action's bytes: the
money-edit test changes exactly one verified field and asserts the diff reports
only the money region plus the recomputed checksum (nothing else). That is the
exact property a user relies on when they supply real before/after saves to
locate the item inventory or stat block.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dmw3editor.core import memcard as mc
from dmw3editor.core.save import DMW3Save
from dmw3editor.core import diff as diffmod

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
USA = SAMPLES / "USA_save.bin"


@pytest.fixture
def record():
    return DMW3Save(USA.read_bytes())


def _payload_from_record(rec: DMW3Save) -> bytes:
    return rec.to_bytes()


def test_noop_diff_is_empty(record):
    a = _payload_from_record(record)
    d = diffmod.diff_payloads(a, a)
    assert all(not sd.deltas for sd in d)


def test_single_money_change_isolates_only_money_plus_checksum(record):
    before = _payload_from_record(record)
    rec = DMW3Save(before)
    rec.set_money(0, 12345)
    after = rec.to_bytes()

    d = diffmod.diff_payloads(before, after)
    # d[0] is the payload header (slot -1), slots follow at d[1..3]
    header = d[0]
    assert {dl.known_as for dl in header.known} == {"payload.checksum (u8)"}
    slot0 = d[1]
    # Money + the recomputed checksum are the only differences.
    labels = {dl.known_as for dl in slot0.known}
    assert labels == {"slot1.money (u32)"}, labels
    assert not slot0.unknown, [dl.known_as for dl in slot0.unknown]
    assert slot0.total_changed == 3  # low 3 of 4 money bytes changed
    assert header.total_changed == 1  # only the low checksum byte changed


def test_single_party_change_isolates_party_fields_only(record):
    before = _payload_from_record(record)
    rec = DMW3Save(before)
    rec.set_party_member(1, 0, 6, 50)  # slot2, pos0 — Guilmon (USA id 6)
    after = rec.to_bytes()

    d = diffmod.diff_payloads(before, after)
    slot1 = d[2]  # slot 2 is index 2 in the returned list
    labels = {dl.known_as for dl in slot1.known}
    # party id+level for pos0 changed (set_party_member on pos 0),
    # each as its own precise field.
    assert labels == {"slot2.party[0].id (u32)", "slot2.party[0].level (u16)"}, labels
    assert not slot1.unknown
    assert {dl.known_as for dl in d[0].known} == {"payload.checksum (u8)"}


def test_format_report_contains_known_labels():
    rec = DMW3Save(USA.read_bytes())
    before = rec.to_bytes()
    rec.set_money(0, 999)
    after = rec.to_bytes()
    report = diffmod.format_report(diffmod.diff_payloads(before, after))
    assert "slot1.money (u32)" in report
    assert "payload.checksum (u8)" in report
