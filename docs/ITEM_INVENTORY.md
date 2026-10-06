# ITEM INVENTORY — CONFIRMED (2026-09-02, controlled in-game diff)

> **STATUS: CONFIRMED FINDING.** This is the original evidence writeup for the
> item inventory and the chunk-2 checksum discovery. It is kept as the record
> of how the array was proven. The current consolidated format spec is
> `SAVE_FORMAT.md`; the editor ships this (Items / Weapons / Armor /
> Accessories / Card Packs tabs). Some later notes below (e.g. "name mapping in
> progress") are superseded by the shipped decomp-backed name table.

## The finding
The DMW3 item inventory is a **byte-per-item QUANTITY array at payload 0x03A7**
(= card 0x05A7). Index 0 = item ID 0. Buying 1 Power Charge (12 bits, heals
500) in DuckStation incremented byte 0x03A7 from 58 -> 59, and the player's
in-game item screen confirmed **59 Power Charges**.

## The oracle
The player's in-game item menu is ground truth. Confirmed byte-exact for
indices 0-24:
  Power Charge 59, Super Charge 51, Ultra Charge 51, Max Charge 50,
  HP Chip 51, MP Chip 51, Power Chip 52, Armor Chip 50, Mind Chip 51,
  Wisdom Chip 50, Boost Chip 50, Charisma Chip 50, Fire Chip 50,
  Water Chip 50, Ice Chip 50, Wind Chip 51, Thunder Chip 50, Metal Chip 50,
  Devil Chip 50, TP Chip 1 50, TP Chip 2 50, TP Chip 3 50, TP Chip V 50,
  Antidote Disk 50, Revive Disk 50.

## Why this was missed before
The maxed USA card has chips stacked at 99 AND party at Lv99, making the same
bytes read as both "item qty 99" and "digimon level 99" — a coincidence that
sent earlier analysis down the level-array path. The EUR card (party Lv99 but
consumables 50-52) broke the tie.

## Array extent & player variance
- EUR player (captures/after_ITEM.mcr): ~50 of nearly every item — they
  bulk-bought the whole equipment catalog (8 pages weapons, 5 armor, 5
  accessories). Quantity array nonzero to about index ~350 (payload ~0x04F5).
- USA (samples/USA_dexdrive.gme): normal playthrough, varied counts (0-4,
  some 99) — player-owned data, confirms the array is inventory not a table.
- The quantity array ends ~idx 350; a gap, then idx 800+ is a DIFFERENT dense
  table (card collection / techs) — NOT items.

## Name-order status
- Indices 0-24: CONFIRMED (screen oracle above).
- The full 352-slot name list is now implemented from the decomp ItemId table
  (save slot = enum idx - 35), shipped in the editor. Subclass boundaries were
  confirmed by live block tests: items 0-48, weapons 49-171, armor 172-248,
  accessories 249-316, card packs 317-351.

## Editor impact
- The editor's Items / Weapons / Armor / Accessories / Card Packs tabs
  read/write bytes at 0x03A7 + slot across the 352-slot array.
- **CRITICAL — CHUNK 2 CHECKSUM:** the save is CHUNKED. Chunk 2's header is at
  **payload 0x0300** (u16 checksum, u16 version @0x0302). Its checksum is the
  SAME XOR8 algorithm over **[0x0304, 0x29C4)**, verified on USA (0x8C),
  EUR-before (0x49), and EUR-after-item-buy (0xBD) — three independent cards.
  The item array at 0x03A7 is INSIDE chunk 2, so ANY item edit MUST recompute
  u16@0x0300 = XOR8 over [0x0304, 0x29C4). Chunk 1 (u16@0x0200 over
  [0x0204,0x0300)) covers the header/party/time region.
- The earlier note in this file saying "no checksum to recompute for items"
  is WRONG — corrected 2026-09-02 by the chunk-2 discovery.
- Both checksums are recomputed automatically by `to_bytes()` /
  `recompute_all()`; see `dmw3editor/core/checksum.py`.
