# DMW3 Save — ORCHESTRATOR CORRECTION v4 (AUTHORITATIVE)
> **STATUS: HISTORICAL — SUPERSEDED.** Superseded by SAVE_FORMAT.md.
> Kept for history only. Current format truth: `SAVE_FORMAT.md`.

Supersedes ADDENDUM_V2 and CORRECTION_V3 where they conflict. Two further
errors of mine are corrected here. Read this one.

## Error 1 — the "record signature" is NOT a signature. It is DATA.

I claimed `13 40 2B 01 01 0D 0D 00` at 0x0208 was a party-record signature at
0x44 spacing. **Withdrawn.** The EUR card has completely different bytes at the
same offset:

```
USA 0x0208: 13 40 2B 01 01 0D 0D 00   -> ".@+....."
EUR 0x0208: 17 3C 35 30 36 39 00 00   -> ".<5069.."
```

`35 30 36 39` is ASCII **`"5069"`** — a short, player-typed string. So
**0x0208 is very probably the PLAYER NAME field** (or a name + small fields),
not a structural magic. The USA bytes are the same field holding a name in a
non-ASCII/custom encoding, or holding different data entirely.

The 0x44 repetition in the USA card was USA-specific data that happened to
repeat; it is NOT a universal record stride. Treat the 68-byte party-record
array as **UNCONFIRMED** and re-derive it from the EUR card as a control.

## Error 2 — header word differs between cards (likely a VERSION)

```
USA 0x0200: E8 00 03 00  'DMW3'   -> u16 @0x200 = 232, u16 @0x202 = 3
EUR 0x0200: 5A 00 04 00  'DMW3'   -> u16 @0x200 =  90, u16 @0x202 = 4
```
`DMW3` at 0x0204 is CONFIRMED on both cards (exactly one occurrence each).
The u16 at **0x0202 = 3 (USA) / 4 (EUR)** is PROBABLY a format/version number,
and the u16 at **0x0200 = 232 / 90** is PROBABLY a length, count, or checksum —
resolve which. An editor must not blindly assume the USA layout applies to EUR
if the version word differs.

## Error 3 — the two cards do not even have the same amount of party data

Populated 0x44-aligned windows from 0x0208:
- USA: indices 0-11, then 17-19
- EUR: index 0, then 3-11, then 13-19 (index 1 and 2 are ENTIRELY ZERO)

EUR's zeroes at indices 1-2 where USA has full data is consistent with EUR being
a much earlier save with fewer party members, but it also means **any field map
derived only from USA is unvalidated.** Every offset claim must be checked
against BOTH cards, and where EUR is zero, say "unvalidated on EUR".

## What still stands (CONFIRMED, both cards)
- Card container, directory, 4-block/32,768-byte payload, region ids
  `BASLUS-01436` (USA) / `BESLES-03936` (EUR) / `BISLPS-03446` (JPN, from the
  game exe SLES_039.36 at 0x9FC/0xA14/0xA2C).
- Payload 0x0000-0x01FF = PS1 title/icon frame.
- Save record starts at **0x0200**; `DMW3` tag at **0x0204**, exactly once.
- USA carries two redundant copies at 0x2900 / 0x5000 (B vs C differ by 6 bytes);
  EUR carries none. Not three in-game slots.
- No HP `current <= max` u16 pair exists anywhere.
- u32 at 0x0228 = 0x0098964F = **9,999,951** on USA (just under a 9,999,999 cap
  => a decimal-capped counter). EUR at the same offset = 0x0098967F = 9,999,999
  exactly. Both are capped counters — strong MONEY/EXP candidates.

## Method mandate — this is why I keep being wrong
Single-sample reverse engineering produces confident nonsense. **Every claim
must be tested against BOTH cards.** A pattern present in USA and absent in EUR
is data, not structure. Find the field that must appear once per instance and
COUNT it. Report what fails to validate — negative results are how this project
stays honest.
