# DMW3 Save Format (AUTHORITATIVE)

> **2026-10-06: the card/container layout, the `MemCardFile`/`MemCardSave`
> header and BOTH checksums were re-derived from the matching decompilation.
> See `docs/MEMCARD_FORMAT.md` — it is now the reference for those parts and
> corrects the record-header and chunk-extent notes below. The sections after
> "Three in-game save slots" remain the field inventory (items, cards, key
> items, per-Digimon stats, DV).**

Current as of 2026-09-03. Verified against the two sample cards
(`samples/USA_dexdrive.gme`, `samples/EUR_raw.mcr`), controlled in-game diffs,
and the official decompilation (`github.com/markisha64/ddw3`). This document
supersedes all earlier format notes (GROUND_TRUTH, ADDENDUM_V2, CORRECTION_V3,
CORRECTION_V4) and the earlier V5 text that incorrectly said the item
inventory was unlocated and that no checksum covered data past 0x0300.

The constants below live in `dmw3editor/core/save.py` and
`dmw3editor/core/checksum.py`; that code is the executable form of this spec.

## Container (CONFIRMED)

- 128 KiB PS1 card, 16 x 8192 B blocks; block 0 = header + 64 x 128 B directory.
- DMW3 entry = 4 blocks = 32,768 B payload. Save names: `BASLUS-01436DMW3-USA`,
  `BESLES-03936DMW3-EUR`.
- `.gme` (DexDrive) = 3904-byte header + raw card. `.vgs`/`.vmp` handled too.
- Payload 0x0000-0x01FF = PS1 title frame (`SC` magic, Shift-JIS title, icons).
- Region = format version **u8** at 0x0202 (3 = USA, 4 = EUR). The editor
  supports USA and EUR saves only. The file is `0x200` header + `0x100` info
  section + three `0x2700` data sections — see `docs/MEMCARD_FORMAT.md` §2.

## Checksums — TWO chunks, XOR8, ONE BYTE each (corrected 2026-10-06)

The save is chunked. Both chunks use the same XOR8 algorithm and each stored
checksum is a single byte (the game's `computeChecksum` returns `u8`).

| Chunk | Header | Checksum covers | Recompute after |
|---|---|---|---|
| 1 (info section) | u8 @ 0x0200 | bytes [0x0204, 0x02D4) | any edit in [0x0204, 0x02D4) |
| 2 (data section 0) | u8 @ 0x0300 | bytes [0x0304, end) | any edit in [0x0304, end) |

`end` is region-specific: **0x29BC on USA, 0x29C4 on EUR** (`GAME_SAVE_SIZE`
0x26BC vs 0x26C4, `stgmcard.h`). The old note used 0x29C4 for both, which fails
(and would rewrite) a live USA card whose [0x29BC, 0x29C4) bytes are non-zero —
the live USA card stores 0xBA, correct only for 0x29BC. The old "u16" was also
wrong: the checksum occupies one byte and the u16 write zeroed `last` (0x0201).
`checksum.py` now writes one byte each and picks `end` from the payload version.
See `docs/MEMCARD_FORMAT.md` §7.

## Record header at 0x0200 (corrected 2026-10-06)

`MemCardFile` (`stgmcard.h:90-97`) — five single-byte/word fields, not a u16 pair:

| Offset | Type | Meaning |
|---|---|---|
| 0x0200 | u8 | info-section checksum (XOR8 of [0x0204, 0x02D4)) |
| 0x0201 | u8 | `last` — the slot last saved to (0..2) |
| 0x0202 | u8 | format version: USA = 3, EUR = 4 |
| 0x0203 | u8 | `unk3` (0 on both regions) |
| 0x0204 | char[4] | ASCII `DMW3` (validity tag, occurs exactly ONCE) |

## Three in-game save slots at 0x0208 / 0x024C / 0x0290 (CONFIRMED)

Stride 0x44 (68 B). Independent slots, proven by differing play times (USA:
199h43m45s / 199h42m43s / 199h41m31s) and rotating party order. A slot of all
zeroes = empty.

### Decoded fields (relative to slot start)

| Offset | Type | Field |
|---|---|---|
| +0x00 | u8[8] | slot/player name area (field data, not a signature) |
| +0x18 | u32 | save's AREA index (decomp stgmcard.c:167) — NOT a partner |
| +0x1C | u32 | save's SHOP index (decomp stgmcard.c:168) |
| +0x20 | u32 | money / Bits (cap 9,999,999) |
| +0x28 | u16 | play time hours |
| +0x2A | u16 | play time minutes |
| +0x2C | u16 | play time seconds |
| +0x30 | u32 | party Digimon id 1 |
| +0x34 | u32 | party Digimon id 2 |
| +0x38 | u32 | party Digimon id 3 |
| +0x3C | u16 | party level 1 |
| +0x3E | u16 | party level 2 |
| +0x40 | u16 | party level 3 |

Party ids are positionally paired with levels (USA reorders ids to 7,8,6 and
levels to 99,99,98 in lockstep). Party slots accept only the 8 base rookies;
the id space is **region-INDEPENDENT**: id 3..10 = Kotemon..Patamon on both
regions, because the record stores the decomp's `Partner.unlocked` value
(`= partner index + 3`; stgmcard.c:1106, game_state.h:193). 0 = empty/locked.
(An earlier "USA ids 1..8" note was wrong and decoded USA cards shifted.)
Note +0x18 is NOT the partner: it is the save's AREA-name index.

**Editor / in-game status (2026-10-06, corrected).** These `+0x30` fields are the
info-section **summary** copy of the party, and the game does NOT run the party
from them — it loads the data section (`stgmcard.c:1027`). The summary stores
ids (`Partner.unlocked`, 3..10); the data-section `GameState.party[3]` at
payload `0x0370` stores indices (0..7). A party swap that writes only the
summary changes the card list but leaves the loaded party untouched — the
reported bug. `DMW3Save.set_party_member` now writes **both** copies (summary
id + level, data index + `Partner.unlocked` + `STAT_LEVEL`). See
`docs/MEMCARD_FORMAT.md` §5.2 for the decomp citations and the byte-level
evidence.

## Key items — 48 flags (CONFIRMED 2026-09-02)

In the game's Important-screen order (the screen oracle read 35 of them
byte-exact). Three disjoint storage areas:

| Block | Payload range | Count |
|---|---|---|
| A | 0x0380..0x03A6 | 39 |
| Monmon DDNA | item-array slot 317 (= 0x04E4) | 1 |
| B | 0x0507..0x050E | 8 |

`key_item_offset(key_index)` maps Important-screen index 0..47 to the flag
byte. 1 = owned, 0 = not.

## Item inventory — byte-per-item quantity array (CONFIRMED 2026-09-02)

- Base: **payload 0x03A7** (`ITEM_BASE`), 352 slots (`ITEM_COUNT`), 1 byte
  each, values 0..99. Index 0 = item id 0.
- Proven by controlled in-game diff: buying 1 Power Charge moved byte 0x03A7
  from 58 to 59, confirmed on the player's item screen.
- Slot naming follows the decomp ItemId enum with an offset of 35
  (save slot = enum idx - 35). Subclass boundaries (confirmed by live block
  tests):

| Subclass | Slots |
|---|---|
| Items | 0..48 |
| Weapons | 49..171 |
| Armor | 172..248 |
| Accessories | 249..316 |
| Card Packs | 317..351 |

- The array ends about index 350; index 800+ is a different dense table
  (card collection / techs), NOT items.

## Card collection — 314 counts (CONFIRMED 2026-09-02)

- Base: **payload 0x06A3** (`CARD_BASE`), 314 bytes, values 0..9.
- Anchored by two live in-game reads: index 0 = "Sacred Spear",
  index 50 = "White Remove".

## Per-Digimon stats — 8 records (CONFIRMED 2026-09-02)

- Records at **payload 0x0A48 + roster_index x 0x3DC** (`DIGI_STAT_BASE`,
  `DIGI_STAT_STRIDE`), 8 records for the 8 base rookies (Kotemon, Kumamon,
  Monmon, Agumon, Veemon, Guilmon, Renamon, Patamon).
- Fields relative to record start (u16 unless noted):

| Offset | Field |
|---|---|
| +0x38 | u32 EXP |
| +0x3C | level |
| +0x3E | max level (99) |
| +0x40 | HP current |
| +0x42 | HP max |
| +0x44 | MP current |
| +0x46 | MP max |
| +0x48 | 13 stats x u16: Strength, Defense, Spirit, Wisdom, Speed, Charisma, Fire, Water, Ice, Wind, Lightning, Machine, Dark |

### Digivolution / DV block (CONFIRMED 2026-09-02/03)

Same record, higher offsets:

| Offset | Type | Meaning |
|---|---|---|
| +0x72 | u16 | header level: the row-1 (primary) digivolution's DV level, e.g. Greymon for Agumon |
| +0x74 | 43 x 20 B | data slots (D_DV_SLOTS, D_DV_SLOT_STRIDE) |

Each 20-byte data slot:

| + | Type | Meaning |
|---|---|---|
| +0..3 | 4 B | leading area (zero padding on natural cards) |
| +4..15 | 12 B | per-form tech/instance record (content) |
| +16..17 | u16 | per-form identity MARKER; 0 = form not earned |
| +18..19 | u16 | DV level for the form in this slot |

- Markers are constant per evolved form and card-independent (44 forms, table
  `DV_FORM_MARKERS` in save.py). Marker 0 is the true "not earned" signal;
  setting a level alone does not display the row in-game (probe-confirmed).
- The DV screen reads a row's techniques from the FOLLOWING slot's content
  field. Slot k's content lives at slot k+1 content (probe-confirmed; header
  row's techs live in slot 0's content). Slot 42's display record is a 43rd
  phantom slot: natural cards show it spilling past the record end
  (`D_DV_SLOT_CONTENT_PHANTOM` = +0x3D4), with 4 of 12 bytes landing in the
  next record's leading zero padding.
- Force-earning writes marker + level and seeds content from the canonical
  lv99 donor harvested from natural cards, zeroing tech pairs whose learn
  threshold exceeds the level (`dv_tech_content`).

## Guarded regions — the editor refuses all writes there

`FORBIDDEN_REGIONS = ((0x2900, 0x5000), (0x5000, 0x7700))`.

These ranges are not fully understood. Note that record 7 of the per-Digimon
array nominally ends at 0x2928 and its DV phantom write can reach 0x292C on
cards whose 8th record is fully populated (the genuine USA card has real
DV-marker bytes in 0x2900..0x2928, e.g. Diaboromon marker 151 at 0x2904). The
0x2900 boundary is therefore conservative by design: it is kept until the
upper layout is proven, and any future relaxation must be verified in-game.
See `docs/OPEN_LEADS.md`.

## Current HP / MP

Not stored in the save. Current stats live in RAM while the game runs
(`DIGIMON_CUR_STATS` in the decomp); the save holds profile-derived values and
the per-Digimon current/max pairs above. No stored battle-state fields exist.

## Canonical id tables (from the decompilation)

- 251 Digimon ids (0 = None, 1 = Kotemon ...) — `data/digimon_ids.json`
- 403 item ids (0 = Null, 1 = BalancedPack ...) — `data/item_ids.json`
- 195 enemy ids — `data/enemy_ids.json`
- Card names/art, pack names, item icons — `data/card_ids.json`,
  `card_images.json`, `packs_ids.json`, `item_icons.json`, `key_items_ids.json`
- Digivolution order + header per roster partner — `data/digivolve_orders.json`
- DV tech profiles (per-form tech list + learn thresholds) —
  `data/dv_tech_profiles.json`, donors `data/dv_content_donors.json`
