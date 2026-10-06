# USER STEP-BY-STEP — getting the editor finished
> **STATUS: HISTORICAL — COMPLETED.** Step-by-step capture instructions from
> the pre-ship campaign. The editor is shipped; the item/card/stat/DV findings
> those captures produced are implemented. Kept for history only.

Goal: three controlled-diff capture pairs (ITEM / CARD / STAT). Each pair =
two snapshots of your save, taken before and after ONE in-game action. The
diff isolates exactly which bytes that action changed, which lets the editor
decode the item inventory, card collection, and per-Digimon stat/XP blocks.

Everything on my side is ready. The only manual steps are yours: boot the
game in DuckStation and perform three small actions.

---

## Files (all set up and verified)

| What | Path |
|---|---|
| DuckStation emulator | `C:\Users\space\Downloads\Mini Game project\PSX Portable\duckstation-qt-x64-ReleaseLTCG.exe` |
| EUR disc | `D:\AGENT\DMW3-disc\Digimon World 2003 (Europe) (En,Fr,De,Es,It).cue` (+ .bin) |
| **Live memory card (Slot 1)** | `D:\AGENT\DMW3-disc\EUR_card_live.mcr` ← DuckStation writes saves here |
| Pristine card backup | `D:\AGENT\DMW3-disc\EUR_digimon-world-3.24459.mcr` |
| Capture script | `D:\AGENT\DMW3SaveEditor\capture.ps1` |

The live card is the **EUR 20-hour save** (`BESLES-03936DMW3-EUR`), verified.
It works with the EUR disc. (Your USA 199-hour card needs a USA disc, which
isn't present — the EUR save is actually better for this: early game, fewer
variables, and a clean party to level.)

---

## ONE-TIME SETUP (2 minutes)

1. Launch DuckStation: `PSX Portable\duckstation-qt-x64-ReleaseLTCG.exe`
2. Menu: **Settings → Memory Cards** (or Controllers → Memory Cards).
3. For **Slot 1**, click the folder icon and select:
   `D:\AGENT\DMW3-disc\EUR_card_live.mcr`
   (If DuckStation asks to create/format it, say yes — it may just adopt the
   existing 128 KB card. If it refuses, use the pristine .mcr and tell me.)
4. Menu: **CD-ROM → Change Disc** → select the `.cue` file above.
5. **Boot the game.** It should find the save on the card.
6. In the game, **load your save** (the 20-hour EUR file).

If the game says "file cannot be found" on the load screen, the card isn't
being read — tell me the exact message and I'll fix the card format.

---

## CAPTURE WORKFLOW (repeat 3 times, once per label)

For each label (`ITEM`, `CARD`, `STAT`) do exactly this:

1. In the game, stand at a **save terminal** with your save loaded.
2. Open PowerShell, go to the project, snapshot the BEFORE state:
   ```
   cd D:\AGENT\DMW3SaveEditor
   powershell -ExecutionPolicy Bypass -File .\capture.ps1 before_ITEM
   ```
3. Do **EXACTLY ONE action**, then **save the game** at the terminal:
   - **ITEM**: buy exactly ONE item (any item) at a shop.
   - **CARD**: win ONE card battle (collects one new card) OR open one card pack.
   - **STAT**: win ONE battle that levels up a party Digimon exactly once.
4. **Exit DuckStation completely** (so the .mcr file is flushed/closed).
5. Snapshot the AFTER state:
   ```
   powershell -ExecutionPolicy Bypass -File .\capture.ps1 after_ITEM
   ```
6. **Restore the pristine card** so the next capture starts from the same
   before-state (do this between captures):
   ```
   powershell -ExecutionPolicy Bypass -File .\capture.ps1 restore
   ```

Repeat with `CARD` and `STAT` in place of `ITEM`.

---

## What happens next (automatic)

1. I run `run_captures.py` → it diffs each before/after pair and lists every
   changed byte with its offset.
2. The item/card/stat decoders turn the deltas into verified field mappings.
3. I wire the verified fields into `save.py` + the GUI + tests.
4. Full suite re-run + byte-exact round-trip + a fresh BOOTTEST card.

---

## If you cannot do one of the actions yet

- No card battles available yet? Buy a card pack at a shop if the game sells
  them, or tell me which single-action the current save CAN do and I'll adapt
  (e.g. use an item from the inventory instead — that also isolates the
  inventory write path).
- Level-up is easiest: find any weak enemy and win one battle that levels
  someone once. If a party member is already near max level, fight with a
  lower-level Digimon or use a stat-boost item instead — tell me which.

---

## What NOT to do

- Do NOT save more than once between the before and after snapshots.
- Do NOT do multiple actions before the after snapshot.
- Do NOT load a different save slot between snapshots.
- If you accidentally do two actions, just `restore` and start that label over.
