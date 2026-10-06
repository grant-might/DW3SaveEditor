# Open leads and unresolved questions

Recorded so the work is not lost or re-guessed. This file tracks ONLY what is
still open. Items marked RESOLVED are kept briefly for the record with a
pointer to where the answer now lives; anything marked RESOLVED is shipped in
the editor.

## RESOLVED — item inventory (2026-09-02, controlled in-game diff)

Earlier exhaustive static searches failed because two unrelated playthroughs
cannot isolate a quantity array (1117 statistically indistinguishable
candidates). The controlled diff (buy exactly one item, re-save, diff) settled
it: byte-per-item quantity array at **payload 0x03A7**, 352 slots, and the
inventory/weapons/armor/accessories/packs subclass boundaries. Shipped in the
Items / Weapons / Armor / Accessories / Card Packs tabs. See SAVE_FORMAT.md.

## RESOLVED — checksum coverage past 0x0300 (2026-09-02)

The save is CHUNKED. Chunk 2 header is u16@0x0300 (checksum, version u16@0x0302)
and covers [0x0304, 0x29C4) with the same XOR8 algorithm — verified on three
independent cards (USA 0x8C, EUR 0x49, EUR-after-item-buy 0xBD). The editor
recomputes both chunks on save. See SAVE_FORMAT.md and checksum.py.

## RESOLVED — per-Digimon stat/XP SoA (2026-09-02)

Stat records confirmed at **payload 0x0A48 + idx x 0x3DC** for the 8 base
rookies: EXP, level, max level, current/max HP, current/max MP, and the 13
stats. The old "0x03BC per-Digimon id array" lead from the USA card was a
coincidence of a maxed save (values 98/99 reading as levels) and is dead; the
EUR card contradicted it. See SAVE_FORMAT.md.

## RESOLVED — DV layout and technique display (2026-09-02/03)

43 x 20-byte DV slots per Digimon record at +0x74, per-form identity markers
at slot +16..17 (marker = true "earned" signal), levels at +18..19, and the
DV screen reads a row's techniques from the FOLLOWING slot's content field
(probe-confirmed V3/V5, 2026-09-03). Force-earn writes marker + level + seeded
content. Shipped in the Digivolution tab. See SAVE_FORMAT.md.

---

## OPEN — the 0x2900 write boundary needs a controlled test

The editor refuses all writes in 0x2900-0x7700 (FORBIDDEN_REGIONS). Record 7
of the per-Digimon array nominally ends at 0x2928, and the genuine USA card
carries real DV-marker bytes in 0x2900..0x2928 (e.g. Diaboromon marker 151 at
0x2904, level 1 at 0x2906) — consistent with the 8th Digimon's DV slots and
phantom slot-42 content landing just past the nominal record end. Two readings
are possible:

1. The 0x2900-0x2928 bytes are the 8th Digimon's DV tail (safe to extend the
   writable range to 0x2928), or
2. 0x2900 really begins a distinct structure and the USA card's overlap is a
   coincidence of the maxed save.

The old "0x2900/0x5000 are two near-identical copies" hypothesis from
SAVE_FORMAT V5 is NOT supported by the current byte evidence (the bytes at
0x2904 decode as a DV marker/level pair, not a header) and should be treated
as obsolete until a controlled experiment says otherwise. Resolving this needs
one probe: write a DV level into record 7's slot 41 on a card where slot 41 is
earned, boot in-game, and see whether the DV screen shows the expected form
and the game accepts the save. Do NOT relax the guard before that test.

## OPEN — chunk structure past 0x29C4

Chunk 2's covered range ends at 0x29C4. A further chunk-header shape appears
right after (0x29C0 region), but its extent is not verified. Absence of
evidence from two cards is not proof of no protection; the editor does not
write there.

## OPEN — layout beyond 0x2928 / inside 0x5000-0x7700

Not understood. The editor refuses writes there. The genuine USA card has
nonzero data through 0x77FF (three-slot-era theory disproved; actual meaning
unknown). EUR ends early (~0x29C3), so USA-only density is not evidence of a
second structure by itself.

## OPEN — canonical fixture cards (waiting on user)

A fresh EUR and a fresh USA memory-card save made on a fresh game boot will be
dropped in as `samples/EUR_fresh.mcr` and `samples/USA_fresh.mcr` canonical
round-trip/region fixtures, with tests alongside the existing samples. Not
started; user will create them later.
