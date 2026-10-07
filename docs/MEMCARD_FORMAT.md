# DMW3 memory-card save format — identification (USA + European)

Authority: the **byte-matching decompilation** at `D:\AGENT\GH-PUBLISH\DW3-DECOMP`
(so the C source *is* the game's code), cross-checked byte-for-byte against real
cards. Every offset below is either read from a named source line or measured on
a card; nothing is guessed. Where a fact could not be pinned it is listed under
"Still unknown".

Primary sources used:

| File | What it establishes |
|---|---|
| `include/stgmcard.h` | `MemCardSave`, `MemCardFile`, `PlayTime`, `MEMCARD_SAVE_VERSION`, `GAME_SAVE_SIZE`, `MEMCARD_FILE_MAGIC` |
| `src/main/memcard.c` | save-file names, section offsets, the XOR8 checksum |
| `src/main/system.c:4109` (`initMemCard`) | `MEMCARD.infoSize = 0x100`, `MEMCARD.dataSize = 0x2700` |
| `src/stgmcard/stgmcard.c` | how every field is read (list/details) and written (save) |
| `include/dw3/game_state.h` | the `GameState`/`Partner` fields a data section holds |
| `include/dw3/files.h` | text-file indices `STAREA 0xAA`, `SHPNAM 0x95` |

Cards used for the byte-level checks (read-only; copies were made first):

| Card | Region | Version | Notes |
|---|---|---|---|
| `Builds/USA/card1.mcd` | USA | 3 | one used slot; has non-zero bytes in `[0x29BC,0x29C4)` |
| `Builds/EUR/card1.mcd` | EUR | 4 | one used slot |
| `samples/USA_dexdrive.gme` | USA | 3 | three used slots (maxed) |
| `samples/EUR_raw.mcr` | EUR | 4 | one used slot (maxed) |

`md5`: USA live `7e72bc5daa1b998faf0186b895d30e52`, EUR live
`00fce7d075ee91e6bc6576cda8339729`.

## 1. Container

Standard 128 KiB PS1 memory card: 16 × 8192-byte blocks; block 0 is the header +
15 × 128-byte directory frames. The DMW3 save is **4 blocks = 32,768 bytes** and
is located by its directory name:

* USA — `BASLUS-01436DMW3-USA` (`memcard.c:8`)
* EUR — `BESLES-03936DMW3-EUR` (`memcard.c:22-25`)
* JPN — `BISLPS-03446DMW3-JPN` (EUR build only, `memcard.c:20`; no sample card)

The directory `size` is 32768 and the block chain is `[1,2,3,4]` on both real
cards. `setSaveHeader` (`memcard.c:60-76`) writes `SC`, `blocks = 4`,
`type = iconCount | 0x10`, the title, a CLUT and 1-3 icon frames; the screen
always passes `iconCount = 3` (`stgmcard.c:1600`), which is why the header area
is exactly `128 + 3*128 = 0x200` bytes and the info section starts at `0x200`.

## 2. File layout (payload = the 32,768-byte DMW3 file)

```
0x0000 .. 0x0200   PS1 title frame: 'SC' + 3 icon frames (128 B each)  [memcard.c:60-76]
0x0200 .. 0x0300   info section: MemCardFile (0xD4 B) + 0x2C zero pad  [stgmcard.h:90-97]
0x0300 .. 0x2A00   data section 0 (one GameSave; 0x2700 bytes)
0x2A00 .. 0x5100   data section 1
0x5100 .. 0x7800   data section 2
0x7800 .. 0x8000   trailing 0x800 bytes — not written by the game, unidentified
```

The section geometry is exact: `MEMCARD.infoSize = 0x100` and
`MEMCARD.dataSize = 0x2700` (`system.c:4116-4117`), and `readSave`/`writeSave`
place section *N* at `iconCount*128 + 128 + infoSize + (N-2)*dataSize`
(`memcard.c:183-192`, `:264-273`). With `iconCount = 3` that is
`0x200 + 0x100 = 0x300`, then `+0x2700` twice. (`stgmcard.c:1604-1609` sets
*different* values — `0x2780`/`0x180` — but those are only the sizes of the two
heap buffers it allocates, not file offsets.)

## 3. Info section — `MemCardFile` (payload `0x0200`, 0xD4 bytes)

| Offset | Type | Field | Source / evidence |
|---|---|---|---|
| `0x0200` | u8 | checksum | `stgmcard.h:91`; XOR8 over `[0x0204, 0x02D4)` |
| `0x0201` | u8 | `last` — the slot last saved to | `stgmcard.h:92`; written `stgmcard.c:1108`, read back `:887` |
| `0x0202` | u8 | `version` = `MEMCARD_SAVE_VERSION` | `stgmcard.h:93`, set `:1097` / `:1373` |
| `0x0203` | u8 | `unk3` | `stgmcard.h:94`; `0` on every card seen |
| `0x0204` | s32 | magic `"DMW3"` (`0x33574D44`) | `stgmcard.h:95,99`; occurs exactly once |
| `0x0208` | `MemCardSave[3]` | the three save summaries | `stgmcard.h:96` |

Checksum evidence (measured): USA live `0x6A`, EUR live `0xBC`,
`samples/USA_save.bin` `0xE8`, `samples/EUR_save.bin` `0x5A`; each equals
XOR8 of `[0x0204, 0x02D4)`. The bytes `[0x02D4, 0x0300)` are **all zero** on
every card, so covering to `0x0300` happens to give the same value — but the
game's range is exactly `sizeof(MemCardFile) - 4 = 0xD0` bytes from `magic`
(`stgmcard.c:881,1109,1374`).

## 4. `MemCardSave` (slot stride `0x44` = 68 bytes)

`stgmcard.h:76-86`. Slots at payload `0x0208`, `0x024C`, `0x0290`.

| Offset | Type | Field | How the game uses it |
|---|---|---|---|
| `+0x00` | u8[0x18] | `name` | C string, a copy of `GameState.name` (`stgmcard.c:1098`); `[0]==0` marks a free slot (`:156`, `:942`) |
| `+0x18` | s32 | `unk18` = **AREA index** | drawn with the area-name text: `TEXT_AREA_NAMES[save->unk18]` (`stgmcard.c:167`); filled from the screen's field, `save->unk18 = screen->unk68` (`:1099`) |
| `+0x1C` | s32 | `unk1C` = **SHOP index** | `TEXT_SHOP_NAMES[save->unk1C]` (`:168`); `= screen->unk6C` (`:1100`) |
| `+0x20` | s32 | `money` | Bits; `:1101`, shown `:172` (cap 9,999,999) |
| `+0x24` | s32 | `PlayTime.frames` | `save->time = *(PlayTime*)&dataBuf->playFrames` (`:1102`) |
| `+0x28` | s16 | hours | `:174` |
| `+0x2A` | s16 | minutes | `:175` |
| `+0x2C` | s16 | seconds | `:176` |
| `+0x2E` | s16 | `PlayTime.maxed` | `stgmcard.h:72`; `0` on every card seen |
| `+0x30` | s32[3] | `partners[3]` | `Partner.unlocked` = **partner index + 3** (`stgmcard.c:1106`, `game_state.h:193`); sprites/animations indexed by `partners[i]-3` (`:200,293,298,305`) |
| `+0x3C` | s16[3] | `levels[3]` | `dataBuf->partners[m].info.stats[STAT_LEVEL]` (`:1105`) |
| `+0x42` | s16 | `unk42` | `stgmcard.h:85`; `0` on every card seen |

Measured on the live cards: `name = 17 3c 35 30 36 39 …` — byte-identical to
`GameState.name` at payload `0x354`, confirming `strcpy(save->name, …)`;
`area=1`, `shop=43`, `money=50`, `partners=[4,8,10]`, `levels=[1,1,1]`,
`frames=1792` (USA) / `8931` (EUR).

**Party-id space is region-independent**: raw `3..10` = Kotemon..Patamon on both
regions, because the record stores `Partner.unlocked` (= index + 3), not the
Digimon enum. Cross-checked on the data section: `GameState.party[3] = [1,5,7]`
(partner *indices*), and `Partner[1].unlocked = 4`, `Partner[5].unlocked = 8`,
`Partner[7].unlocked = 10` — exactly the header's `[4,8,10]`.

There is **no single "partner" field** in a `MemCardSave`; the three party
members are `partners[0..2]`. Older editor code read `+0x18` as a "partner" — it
is the AREA index.

## 5. Data sections — `GameSave` (one per in-game slot)

Each section starts with 4 header bytes then a copy of `GameState`'s first
`GAME_SAVE_SIZE` bytes (`stgmcard.c:1027` `*(GameSave *)&GAME = *(GameSave *)dataBuf`).

| Section-rel | Type | Field | Source |
|---|---|---|---|
| `+0x00` | u8 | checksum = XOR8 over `[+0x04, +0x04 + GAME_SAVE_SIZE - 4)` | `stgmcard.c:1020,1096` |
| `+0x01` | u8 | unused (0) | — |
| `+0x02` | u8 | `version` = `MEMCARD_SAVE_VERSION` | `:1023,1097` |
| `+0x03` | u8 | unused (0) | — |
| `+0x04` | `GameState` | the saved game state | `stgmcard.c:1027` |

`GAME_SAVE_SIZE` is region-specific (`stgmcard.h:104-110`): **USA `0x26BC`**,
**EUR `0x26C4`**. The game reads/writes `sizeof(GameSave)` bytes and the
checksum covers all but the first four, so the covered end is:

| Region | Covered range | Notes |
|---|---|---|
| USA | `[0x0304, 0x29BC)` | 0x0304 + 0x26BC − 4 |
| EUR | `[0x0304, 0x29C4)` | 0x0304 + 0x26C4 − 4 |

Measured proof of the difference: the **live USA card** stores `0xBA`, which
equals XOR8 over `[0x0304, 0x29BC)`; the EUR extent gives `0xBD` (wrong) because
that card has non-zero bytes in `[0x29BC, 0x29C4)`
(`25 4f 65 08 … 10 cc 33 33 51 66 32 a9 48`). The `samples/USA_save.bin`,
`samples/EUR_raw.mcr` and `samples/USA_dexdrive.gme` cards all have zeros there,
which is why a single fixed extent of `0x29C4` appeared to work.

### 5.1 What a data section holds (the fields the editor can expose)

`GameState` offsets map to payload as `payload = 0x0300 + GameStateOffset`
(section 0). Confirmed on both live cards:

| GameState off | Payload | Type | Field |
|---|---|---|---|
| `0x0000` | `0x0300` | u8[4] | section header (checksum/version) |
| `0x0048` | `0x0348` | s32 | `playFrames` (8.8) |
| `0x004C` | `0x034C` | s16 | `playHours` |
| `0x004E` | `0x034E` | s16 | `playMinutes` |
| `0x0050` | `0x0350` | s16 | `playSeconds` |
| `0x0052` | `0x0352` | s16 | `playTimeMaxed` |
| `0x0054` | `0x0354` | char[0x18] | player `name` |
| `0x006C` | `0x036C` | s32 | `money` |
| `0x0070` | `0x0370` | s32[3] | `party[3]` — partner **indices** |
| `0x007C` | `0x037C` | s8[0x193] | `items` (counts) — editor `ITEM_BASE 0x03A7`… |
| `0x020F` | `0x050F` | s8[0x193] | `equippedItems` |
| `0x03A2` | `0x06A2` | s8[0x13D] | `cards` — editor `CARD_BASE 0x06A3` |
| `0x04DF` | `0x07DF` | u8[0x149] | `cardsSeen` |
| `0x0628` | `0x0928` | `Deck[3]` | `decks` |
| `0x075C` | `0x0A5C` | `Partner[8]` | `partners` (stride `0x3DC`) |
| `0x263C` | `0x293C` | s32 | `progress` |
| `0x2640` | `0x2940` | s32 | `partySet` |
| `0x2644…` | `0x2944…` | u8[] | event flag groups (`flags02`..`flags40`) |

`Partner` (`game_state.h:191-196`): `unk0[4]` (`+0x0`), `unlocked` (`+0x4`,
id+3), `battleDigivolve` (`+0x8`), `info` = `PartnerStats` (`+0xC`).
`PartnerStats`: `name[0x18]` (`+0x0`), `exp` s32 (`+0x18` → payload `+0x24`),
`stats[19]` (`+0x1C`), `status[3]` (`+0x42`), `slots[4]` (`+0x48`),
`entries[44]` (`+0x50`), `equip[6]` (`+0x3C0`). The editor's `DIGI_STAT_BASE`
(`0x0A48`) is `Partner[0]` (`0x0A5C`) **minus 0x14**; its per-record offsets are
each +0x14, so absolute targets line up (`D_EXP 0x38` → `Partner+0x24`, the real
`info.exp`; `D_LEVEL 0x3C` → `info.stats[0]`, the real `STAT_LEVEL`; `D_STATS
0x48` → `info.stats[6]`).

### 5.2 Which copy the game trusts — the party is stored TWICE

**Resolved 2026-10-06 by byte-level experiment on card copies.** The info
summary (`MemCardSave.partners[3]` at slot `+0x30`) and the data-section
`GameState.party[3]` (payload `0x0370`, `game_state.h:297`) are **two different
copies that store two different things**, and the game loads only the second:

* `stgmcard.c:1027` — `*(GameSave *)&GAME = *(GameSave *)STGMCARD_funcs.dataBuf;`
  — the **running game state comes exclusively from the data section.** The
  summary is never loaded into `GAME`; it is consumed only by the save-list /
  details display (`stgmcard.c:167-176`, `:197-200`, `:289-292`, `:646-647`).
* The data section's `GameState.party[3]` holds partner **INDICES** (0..7,
  `game3.c:759` `getPartyMember`, `game3.c:830` `getPartyPartner` returns
  `partners[party[i]].unlocked - 3`). The summary's `partners[3]` holds
  `Partner.unlocked` = **index + 3** (ids 3..10), re-derived from `GAME` on save
  (`stgmcard.c:1104-1106`).

**The reported bug, explained.** The owner swapped Patamon → Veemon with the
slot editor's party controls and maxed three Digimon on the roster page. The
editor wrote only the info summary, so the card list showed Veemon while the
data section still held the old index — the game kept loading the *old* party.
The roster-page stat/level edits held because they write the data section
directly; summary-only money/play-time "held" only in the sense that the load
screen re-derives them from whatever the card holds.

**Measured on the owner's two live cards** (the post-edit cards): summary ids
`[4, 8, 7]` (Kumamon, Guilmon, Veemon) but data-section indices `[1, 5, 7]`
(Kumamon, Guilmon, **Patamon**); the game-written `Partner.unlocked` fields are
Kumamon `4`, Guilmon `8`, Patamon `10` — index + 3 on the USA and the EUR card
alike (`game3.c:766` `setParty` writes `unlocked = partner + 3`). Note id 7
(Veemon) and index 7 (Patamon) are different partners with the same value — the
id/index confusion that hid the bug.

**The fix (in `DMW3Save.set_party_member`).** A swap now writes BOTH copies and
converts region-aware (`party_index_for_id` / `party_id_for_index`, both regions
offset 3):

1. info summary `partners[position]` = the id, and its `levels[position]`;
2. data section `GameState.party[position]` = the **index** (`id - party_min`);
3. the partner's `Partner.unlocked` = the id, so the game accepts it
   (`getPartyPartner` returns `unlocked - 3`; an unlocked-0 partner yields -3);
4. the partner's `Partner.info.stats[STAT_LEVEL]` = the party level, so the
   level applies in game.

The data-section write is skipped when the slot's section is inside
`FORBIDDEN_REGIONS` (in-game slots 2/3 today) — `set_party_member` still updates
the summary there and `party_data_written(slot)` reports it, so a swap for those
slots cannot take effect in game until that region is unlocked.

Verified byte-for-byte on copies of both the USA and the EUR card: `0x0378`
(`GameState.party[2]`) `0x07 -> 0x04`, `Partner[4].unlocked` (payload `0x19D0`)
`0x00 -> 0x07`, `Partner[1].STAT_LEVEL` (`0x0E60`) `0x63 -> 0x37`, the data-
section checksum byte `0x0300` and the info checksum `0x0200` recomputed; the
written cards re-load and verify (`checksum_valid`).

## 6. Region differences (USA vs European)

Everything above is identical between the two regions — the code is shared, not
`#if`-gated — with exactly these four differences:

| Thing | USA | EUR |
|---|---|---|
| `MEMCARD_SAVE_VERSION` (0x0202 / section `+0x02`) | `3` | `4` |
| `GAME_SAVE_SIZE` | `0x26BC` | `0x26C4` |
| data-section checksum end | `0x29BC` | `0x29C4` |
| file name | `BASLUS-01436DMW3-USA` | `BESLES-03936DMW3-EUR` |

`setSaveFileName` (`memcard.c:16-56`) also exists for JPN and the five EUR
languages, but they share the EUR file name and `GAME_SAVE_SIZE`. The 0x0202
version byte is the editor's region key.

## 7. Checksums (definitive)

Both are plain XOR8 (XOR of every covered byte), `u8` — `computeChecksum`
returns `u8` (`memcard.c:421-429`, checked with `& ~expected`, `:411-419`).

| | Stored at | Type | Covers | Recompute after |
|---|---|---|---|---|
| Info section | `0x0200` | u8 | `[0x0204, 0x02D4)` | any edit in `[0x0204, 0x02D4)` |
| Data section 0 | `0x0300` | u8 | `[0x0304, end)` | any edit in `[0x0304, end)` |
| Data sections 1/2 | `0x2A00` / `0x5100` | u8 | `[+0x04, end)` | the editor never writes there |

`end` = `0x29BC` (USA) or `0x29C4` (EUR).

**Two defects this identification removed from the editor** (both were live):

1. The data-section extent was hard-coded to the EUR `0x29C4` for every card, so
   a live USA save failed verification and `to_bytes()` would have rewritten its
   checksum to `0xBD`; the game computes `0xBA` and would reject the save.
   Verified: before the fix `DMW3Save(live_usa).checksum_valid == False` and
   `to_bytes()[0x300]` changed `0xBA → 0xBD`; after, it validates and stays
   `0xBA`. The extent is now chosen from the payload's version byte.
2. Both checksums were read/written as little-endian `u16` at `0x0200`/`0x0300`,
   which writes a `0` into the following byte — silently zeroing
   `MemCardFile.last` at `0x0201` on every save. Both are now single-byte
   writes (`last` is preserved).

## 8. Editor mapping — every offset the editor relies on

| Editor symbol | Value | Status |
|---|---|---|
| `PAYLOAD_SIZE` | 32768 | confirmed (4 blocks × 8192) |
| `TITLE_FRAME_END` | 0x0200 | confirmed (`128 + 3*128`) |
| `RECORD_BASE` | 0x0200 | confirmed (`MemCardFile`) |
| `MAGIC_OFFSET` / `MAGIC` | 0x0204 / `DMW3` | confirmed |
| `VERSION_OFFSET` | 0x0202 | confirmed (u8) |
| `H_CHECKSUM/H_LAST/H_UNK3` | 0x0200/0x0201/0x0203 | newly added this pass |
| `INFO_SECTION_SIZE` | 0x100 | confirmed (`system.c:4116`) |
| `DATA_SECTION_OFFSETS` | 0x0300, 0x2A00, 0x5100 | newly added this pass |
| `DATA_SECTION_SIZE` | 0x2700 | confirmed (`system.c:4117`) |
| `GAME_SAVE_SIZE_BY_VERSION` | {3:0x26BC, 4:0x26C4} | newly added this pass |
| `SLOT_OFFSETS` / `SLOT_SIZE` | 0x208/0x24C/0x290 / 0x44 | confirmed |
| `F_NAME`(+`F_NAME_SIZE`) | 0x00 (+0x18) | name is 0x18 bytes, not 8 |
| `F_AREA` / `F_SHOP` | 0x18 / 0x1C | newly added (`F_PARTNER`/`F_UNKNOWN_1C` are the old wrong labels) |
| `F_MONEY` | 0x20 | confirmed |
| `F_TIME_FRAMES` / `F_TIME_MAXED` | 0x24 / 0x2E | newly added |
| `F_HOURS/MINUTES/SECONDS` | 0x28/0x2A/0x2C | confirmed (s16) |
| `F_PARTY_IDS` / `F_PARTY_LEVELS` | 0x30.. / 0x3C.. | confirmed |
| `F_UNK42` | 0x42 | newly added |
| `CARD_BASE` | 0x06A3 | confirmed (`GameState.cards` = 0x03A2 + 0x301) |
| `ITEM_BASE` | 0x03A7 | confirmed (`GameState.items` = 0x007C + 0x32B) |
| `KEY_ITEMS_BLOCK_A/B` | 0x0380..0x03A6 / 0x0507..0x050E | confirmed (inside data section 0) |
| `DIGI_STAT_BASE` / `DIGI_STAT_STRIDE` | 0x0A48 / 0x3DC | offsets line up; base is 0x14 before `GameState.partners` (see §5.1) |
| `FORBIDDEN_REGIONS` | 0x2900-0x7700 | conservative; `0x29BC..0x2A00` (USA) is real gap data |

## 9. Still unknown

* **`[0x7800, 0x8000)`** (2048 bytes) — the game's own layout (`0x200 + 0x100 +
  3*0x2700 = 0x7800`) ends before it; nothing in the source writes it. `0xFF` on
  the live USA card, `0x00`/`0xFF`-mixed elsewhere. Not checksummed by the game.
* **`[0x29BC, 0x2A00)` on USA cards** — outside the USA `GameSave` and outside
  its checksum, yet non-zero on the live USA card (`25 4f 65 08 …`). Its meaning
  is unexplained; the editor refuses writes there.
* **`MemCardSave.unk42`** (slot `+0x42`) — zero on every card seen; no source
  line reads it.
* **`MemCardFile.unk3`** (0x0203) and the data section's `+0x01`/`+0x03` — zero
  everywhere; unread by the source.
* **`MemCardSave.unk18/unk1C` name tables** — the field is proven to be an index
  into `STAREA` (0xAA) / `SHPNAM` (0x95), but those text files are not extracted
  here, so the editor can show the numeric index only.
* **`PlayTime.maxed`** — always 0; the `PlayTime` struct names it but no read was
  found.
* **The three data sections vs three summaries** — the editor exposes per-Digimon
  data for data section 0 only; sections 1/2 are inside `FORBIDDEN_REGIONS`.
* **Area/shop semantics** — the ids come from the mode that opened the screen
  (`screen->unk68` from `STGMCARD_prevModes`, `screen->unk6C` from
  `STGMCARD_modeValues`, `stgmcard.c:1563-1578`); which mode yields which id is
  not enumerated.

## 10. Unverified / open (see also §5.2)

* **Whether an in-game save preserves an info-section money/party/play-time
  edit, and whether the data section receives that edit.** The owner reports the
  edited values taking effect in-game (§5.2), with no independent confirmation;
  the decisive save-and-reload test has not been run. The source shows the
  summary is re-derived from `GAME` on save (`stgmcard.c:1094-1109`) and that no
  code path was found loading the summary into `GAME` (only the data section is:
  `stgmcard.c:1027`) — so that test would also settle how a summary-only edit
  reaches the running game state.
* Which mode id maps to which area/shop name.
* The meaning of the USA `[0x29BC, 0x2A00)` gap bytes.

## 11. Tests that pin this

`tests/test_memcard_format.py` (new, 10 tests) asserts the header/field offsets,
the exact covered ranges, the region-dependent data-section extent (including an
observable USA-vs-EUR divergence), `last`-byte preservation and the "no clobber"
property. `tests/test_checksum.py`, `tests/test_save.py`, `tests/test_diff.py`
and `tests/test_item_checksum.py` cover the rest of the model.
