# DMW3 Save — ORCHESTRATOR CORRECTION v3 (SUPERSEDES ADDENDUM_V2)
> **STATUS: HISTORICAL — SUPERSEDED.** Part of the RE correction trail
> (see ADDENDUM_V2). Superseded by CORRECTION_V4, then by SAVE_FORMAT.md.
> Kept for history only. Current format truth: `SAVE_FORMAT.md`.

I got this wrong in ADDENDUM_V2 and I am correcting it with evidence. **v3 is
authoritative.** ADDENDUM_V2's "three in-game save slots" claim is WITHDRAWN.

## What is actually true (CONFIRMED)

The 0x2700 repeat period is REAL, but it is **NOT three in-game save slots**.
It is **one logical save record, stored redundantly**.

Evidence:
1. The ASCII `DMW3` tag occurs **exactly ONCE** in the whole 32,768-byte payload,
   at **0x0204**. If there were three equal slots there would be three tags.
   Regions 2 and 3 begin `00 00 65 80 97 00 01 00` — no `DMW3`, no `E8 00 03 00`.
2. Region diffs in USA: A(0x0200) vs B(0x2900) = 156 bytes; A vs C(0x5000) = 154;
   **B vs C = only 6 bytes.** B and C are near-identical to each other and both
   differ from A the same way — the signature of a primary copy plus two
   redundant/backup revisions, not three independent user saves.
3. **EUR is not periodic at all**: EUR A vs B = 4,204 differing bytes, EUR data
   ends at 0x29C3, and 0x2900+ holds only 99 non-zero bytes. EUR contains ONE
   copy. A three-slot layout would appear in both cards; it does not.

## Working model (use this)

| Region | Range | Meaning |
|---|---|---|
| Title frame | 0x0000-0x01FF | PS1 icon/title (`SC` magic, Shift-JIS title, CLUT, icons) |
| **Primary record** | **0x0200 - ~0x28FF** | the live save; header `E8 00 03 00` + `DMW3` at 0x0204 |
| Copy B | ~0x2900 - ~0x4FFF | redundant copy / earlier revision (USA only) |
| Copy C | ~0x5000 - ~0x76FF | redundant copy / earlier revision (USA only) |
| Tail | 0x7700 - 0x77FF | trailing data |

**Edit the PRIMARY record at 0x0200.** Whether copies B and C must be updated in
lockstep is UNRESOLVED and is a real risk — flag it, do not guess. An
editor should offer "mirror edits to backup copies" as an explicit option.

## Still CONFIRMED and unaffected
- Payload = 32,768 B = card blocks 1..4; names `BASLUS-01436DMW3-USA` /
  `BESLES-03936DMW3-EUR`.
- Header `E8 00 03 00` then `DMW3` at payload 0x0204.
- **Active party = 3 records, stride 0x44 (68 B), starting at payload 0x0208**
  (0x0208 / 0x024C / 0x0290), via repeated signature `13 40 2B 01 01 0D 0D 00`
  at exact 0x44 spacing. Offsets are relative to the PRIMARY record base 0x0200.
- No HP `current <= max` u16 pair exists anywhere. Do not assume stored HP/MP.

## The lesson — apply it to your own work
My three-slot claim survived a 98.1% periodicity match and died to a single
`DMW3` tag count. **Periodicity is not identity.** Before you believe a
structural hypothesis, find the field that must appear once per instance and
COUNT it. Verify your own claims the same way, and if you find *this* file
wrong, say so with evidence — that is exactly what I want from you.
