# DMW3 Save — ORCHESTRATOR ADDENDUM v2 (SUPERSEDES parts of GROUND_TRUTH.md)
> **STATUS: HISTORICAL — SUPERSEDED.** Part of the RE correction trail
> (ADDENDUM_V2 -> CORRECTION_V3 -> CORRECTION_V4 -> SAVE_FORMAT.md). The
> three-slot / redundant-copy claims in this file were withdrawn. Current
> format truth: `SAVE_FORMAT.md`. Kept for history only.

All of this is CONFIRMED by the orchestrator with real byte evidence. It
overturns the flat-struct assumption in GROUND_TRUTH.md. Obey THIS file where
the two disagree.

## 1. The payload holds THREE INDEPENDENT IN-GAME SAVE SLOTS
Repeat-period analysis of `USA_save.bin`: best period **0x2700 (9,984 B)** with a
**0.981** byte-match ratio. Slot bases in the 32,768-byte payload:

| Slot | Base    | Size   |
|------|---------|--------|
| 0    | 0x0200  | 0x2700 |
| 1    | 0x2900  | 0x2700 |
| 2    | 0x5000  | 0x2700 |
| tail | 0x7700  | 0x900 (trailing/unused; USA nonzero to 0x77FF) |

Slot0 vs slot1 differ in only **156 of 9,984** bytes and slot0 vs slot2 in 154 —
i.e. three near-identical saves of the same playthrough at slightly different
points. This is why USA "looked" full to 0x77FF: it is 3 populated slots.
EUR has slot0 populated (nonzero to 0x28F6) and slot1+ largely empty.

**Consequence:** the editor MUST present a slot selector, and every field offset
must be expressed as `slot_base + relative_offset`, never as an absolute payload
offset. Any absolute offset above 0x2900 is almost certainly the same field in a
later slot, not a new field.

## 2. Slot header
At slot_base+0x00: `E8 00 03 00` then ASCII **`DMW3`** at slot_base+0x04.
Use the `DMW3` tag at slot_base+4 as the slot-occupied validator.

## 3. The ACTIVE PARTY is a 3 x 68-byte record array
Records start at **slot_base+0x08** with stride **0x44 (68 bytes)**, count 3
(payload 0x208 / 0x24C / 0x290 for slot 0). Found by locating the repeated
8-byte record signature `13 40 2B 01 01 0D 0D 00` at exactly 0x44 spacing.
(A 4th hit at 0x354 is a different structure, delta 0xC4 — do not treat it as a
4th party member without evidence.)

Record 0 raw (68 B) at 0x208:
```
13 40 2B 01 01 0D 0D 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 02 00 00 00 2C 00 00 00
4F 96 98 00 00 33 00 00 C7 00 2B 00 2D 00 00 00
06 00 00 00 07 00 00 00 08 00 00 00 62 00 63 00
63 00 00 00
```
PROBABLE (needs confirmation, do not ship as fact):
- +0x18 `02 00 00 00` and +0x1C `2C 00 00 00` — small u32 counters
- +0x20 `4F 96 98 00` — u32, plausibly EXP
- +0x28 `C7 00` = 199, +0x2A/+0x2C ~0x2B/0x2D — 16-bit stats
- +0x30/+0x34/+0x38 = `06/07/08` u32 — technique or slot IDs; note records 1
  and 2 hold the SAME three values in ROTATED order (07,08,06 / 08,07,06),
  which is a strong hint these are per-member IDs/indices
- +0x3C/+0x40 `62 00 63 00 63 00` = 98/99/99 — near-max stats (late save)

Fields that are IDENTICAL across all three records (e.g. the leading
`13 40 2B 01 01 0D 0D`) are NOT per-Digimon identity fields — most likely
shared/global or a header. Treat differing bytes as the identity/stat payload.

## 4. Method that worked — reuse it
Differential analysis ACROSS THE THREE SLOTS of the same card is far more
powerful than USA-vs-EUR (which compares unrelated playthroughs). Only ~155
bytes differ between slots, so those ~155 offsets are precisely the fields that
changed between three moments of one playthrough: play time, position, progress,
and party state. **Enumerate those differing offsets and you have the volatile
field list handed to you.** Do this.

## 5. Standing rules unchanged
Evidence or silence. CONFIRMED/PROBABLE/SPECULATIVE labels mandatory. Never
write to `samples\`. Fabrication is the one unforgivable failure.
