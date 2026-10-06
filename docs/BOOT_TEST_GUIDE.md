# In-emulator boot test (Task v2b) — USER PLAYTEST
> **STATUS: HISTORICAL — COMPLETED.** In-emulator boot test (task v2b). The
> automated proof lives on in `work/verify_boot_card.py` and the boot test
> card, and the editor has been user-confirmed since. Kept for history only.

Per project rule (`dmw3-port-ops`: "no auto-test bots — user playtests"), the
actual in-game confirmation is yours. The automated half is done:
`work/verify_boot_card.py` proves the edited card is structurally valid and
**checksum-correct** (game will not reject it), and that exactly the intended
bytes changed.

## What was edited (BOOTTEST card)

`work/BOOTTEST_digimon-world-3.21060.gme` — a copy of your USA card with Save
Slot 1 changed:
  * money bumped
  * party Digimon ids injected (Omnimon + 2 others)
  * one party level bumped
Checksum recomputed. Nothing else on the 128 KiB card touched.

## How to boot it

The portable DuckStation at `C:\Users\space\Downloads\duckstation-windows-x64-release`
has NOT been run yet, so it has no `memcards/` dir. Two equivalent ways to load
the card:

### Option A — point DuckStation's memory card at the existing save folder
1. Launch `duckstation-qt-x64-ReleaseLTCG.exe`.
2. Settings → Memory Cards (or Controllers → Memory Card).
3. Set **Slot 1** to the file path:
   `C:\Users\space\Downloads\duckstation-windows-x64-release\Digimon World 3 saves\BOOTTEST_digimon-world-3.21060.gme`
   (copy `work\BOOTTEST_*.gme` into that folder first — see below).
4. Boot the game → load Save Slot 1 → confirm the edited party/levels/money.

### Option B — drop into DuckStation's auto memcard dir
1. Copy `work\BOOTTEST_digimon-world-3.21060.gme` into:
   `C:\Users\space\Downloads\duckstation-windows-x64-release\Digimon World 3 saves\`
2. In DuckStation, assign that card to Slot 1 (it will appear in the folder
   picker once the dir exists).
3. Boot and confirm.

## Copy helper (run from the editor venv)
```
python -c "import shutil; shutil.copy(r'D:\AGENT\DMW3SaveEditor\work\BOOTTEST_digimon-world-3.21060.gme', r'C:\Users\space\Downloads\duckstation-windows-x64-release\Digimon World 3 saves\BOOTTEST_digimon-world-3.21060.gme')"
```

## Pass criteria
* Game loads the card without a "corrupted save" error (proves checksum logic).
* Save Slot 1 shows the injected party / bumped level / bumped money.

If either fails, it points at a wrong offset in `save.py` — report back and I
will re-derive it against the live in-game state.
