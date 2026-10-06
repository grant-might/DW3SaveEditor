# READ ME FIRST — Wave 2
> **STATUS: HISTORICAL — SUPERSEDED.** Wave-2 agent brief. The campaign it
> describes (controlled-diff captures) is complete and its findings are
> shipped. Current format truth: `SAVE_FORMAT.md`.

**`docs/SAVE_FORMAT.md` is the ONLY authoritative format document.** Ignore
`GROUND_TRUTH.md`, `ADDENDUM_V2.md`, `CORRECTION_V3.md`, `CORRECTION_V4.md` —
they are a paper trail of my earlier mistakes, kept only for history.

## The rules that matter

1. **Never invent an offset.** Every claim must be backed by bytes you actually
   read from `samples/USA_save.bin` and `samples/EUR_save.bin`. Quote the hex.
   "Probably at 0x…" is worthless to me; I will check, and I will find it.
2. **Say "I could not determine this."** A short honest report beats a long
   confident wrong one. I have already had to retract four of my own claims.
3. **Verify on BOTH cards.** A field that only works on one card is not solved.
   USA is a late-game save (199 h, all Lv98/99); EUR is early (20 h).
4. **Run the tests before you finish:**
   `cd /d/AGENT/DMW3SaveEditor && QT_QPA_PLATFORM=offscreen ./.venv/Scripts/python.exe -m pytest tests/ -q`
   68 pass, 1 skips. **If your change breaks any of them, fix it or revert it.**
5. Use FORWARD-SLASH paths in bash (`/d/AGENT/...`); backslashes get eaten.
   Interpreter: `/d/AGENT/DMW3SaveEditor/.venv/Scripts/python.exe`.
6. **Do not edit** `dmw3editor/core/checksum.py`, `core/save.py`,
   `core/memcard.py`, `ui/theme.py`, `ui/main_window.py`, or anything in
   `tests/` unless your task explicitly says so — I own those. Add NEW files.
7. Never modify anything in `samples/` or the user's original cards in
   `C:/Users/space/Downloads/duckstation-windows-x64-release/Digimon World 3 saves/`.
   Copy to `work/` first.

## What is already SOLVED — do not redo it

- Container read/write for `.mcr/.mcd/.mc/.bin/.gme/.vgs/.vmp`, all 3 regions.
- Header checksum: `u16 @0x0200 == XOR8 [0x0204,0x0300)`. Verified both cards.
- Three save slots at 0x0208 / 0x024C / 0x0290, stride 0x44, with partner id,
  money, play time h/m/s, and 3 x (party Digimon id u32 + level u16) decoded.
- Canonical id tables from the decompilation (251 Digimon, 403 items, 195
  enemies) in `dmw3editor/data/*.json`.
- A working PySide6 GUI with 3 slot tabs and a hex view.

## Useful assets already on disk

- `work/ddw3/` — sparse clone of the **official decompilation**
  (`github.com/markisha64/ddw3`). `rust/types/src/` has `digimon_id.rs`,
  `item_id.rs`, `enemy_id.rs`, `digimon_profile.rs` (the 0x58-byte stat struct).
  `rust/dw2003_exe_data/src/data.rs` has RAM addresses. `lang_file/` has text.
- `work/disc_extract/SLES_039.36` — the EUR game executable.
- Save id strings live in that EXE at 0x9FC.
