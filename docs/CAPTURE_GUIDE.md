# Controlled-diff capture guide — WHAT THE USER MUST PROVIDE
> **STATUS: HISTORICAL — COMPLETED.** Controlled-diff capture guide. The
> capture campaign it describes was completed 2026-09-02 and the decoders are
> shipped in the editor. Kept for history only.

The item inventory, card collection, and per-Digimon stat/XP blocks CANNOT be
found by static analysis of two unrelated saves (proven: 1117 indistinguishable
item-inventory candidates). The only reliable method is a CONTROLLED DIFF: two
saves that differ by EXACTLY ONE in-game action. That isolates the field with
mathematical certainty.

## Option A — two memory-card saves (EASIEST for the user)
1. Launch DuckStation, load the USA card (`digimon-world-3.21060.gme`).
2. Boot the game, load Save Slot 1.
3. Do EXACTLY ONE action, then save the game to the card (in-game save).
4. Exit DuckStation.
5. Copy the card to `captures/after_<ACTION>.gme`.
6. Repeat from step 3 with a DIFFERENT single action, each time starting from
   the SAME pre-action state (re-copy the original card first so each "after"
   derives from the same "before").

Required capture sets (each = one "before" + one "after"):
- **ITEM**: before buying anything, after buying exactly 1 of one item.
- **CARD**: before, after collecting exactly 1 card (win one card battle / open
  one card pack).
- **STAT/LEVEL**: before, after one battle that levels a party Digimon exactly
  once (or after feeding one stat-boost item).

The "before" can be the SAME original card for all three sets.

## Option B — two DuckStation .sav save-states (MORE POWERFUL — RAM structs)
1. Boot DuckStation, load the card, load Save Slot 1.
2. Press the save-state hotkey (F3 = save state to slot 1 by default).
3. Do EXACTLY ONE action.
4. Save state again (overwrite or to slot 2).
5. Copy both `*.sav` files to `captures/`.

The RAM extractor `research/scripts/06_state_ram.py` turns each `.sav` into a
2 MiB RAM image; diffing the two isolates the live RAM struct for that action.
That maps RAM offset -> in-save offset once we correlate with the card diff.

## Where to drop files
`D:\AGENT\DMW3SaveEditor\captures\`
(Named clearly: before_ITEM.gme / after_ITEM.gme, etc.)

## What the orchestrator will do with them
Run `dmw3editor.core.diff.diff_files(before, after)` per pair -> exact byte
deltas. Then subagents decode each delta region against the decompilation
(`work/ddw3`) id tables and the SoA stride already found at 0x03A7. Validated
fields get wired into `save.py` + GUI + tests.
