# DMW3 Save Editor — Verified Ground Truth (Orchestrator, v1)
# DMW3 Save Editor — Verified Ground Truth (Orchestrator, v1)

> **STATUS: HISTORICAL — SUPERSEDED.** This was the v1 ground-truth doc from
> the reverse-engineering phase. It is kept only as a process record. The
> current authoritative format doc is `SAVE_FORMAT.md`; current usage is
> `USAGE.md`; current open questions are `OPEN_LEADS.md`. Do not follow
> offsets or rules stated here if they conflict with SAVE_FORMAT.md.

Everything here was verified by the orchestrator with real tool output. Do NOT
contradict it without producing evidence (hexdump + offsets). If you find it
wrong, say so loudly with proof.

## Project root
`D:\AGENT\DMW3SaveEditor`
- `.venv\Scripts\python.exe` — Python 3.12.10, **PySide6 6.11.2**, numpy, pytest installed.
  ALWAYS use this interpreter. Bare `python`/`python3` DO NOT EXIST on this host.
- `samples\` — canonical artifacts (read-only, never overwrite):
  - `USA_dexdrive.gme` (134,976 B) — DexDrive container, 3,904-byte header then `MC`
  - `EUR_raw.mcr` (131,072 B) — raw PS1 card image
  - `USA_save.bin`, `EUR_save.bin` (32,768 B each) — extracted save payloads
- `research\` — findings (markdown + JSON)
- `dmw3editor\` — the app package (`core\`, `ui\`, `data\`)
- `tests\` — pytest
- Game disc available: `C:\Users\space\Downloads\duckstation-windows-x64-release\games\Digimon World 2003 (Europe) (En,Fr,De,Es,It).bin`
  (+ `.cue` in `C:\Users\space\Downloads\DMW3Setup\DigimonWorld2003\`)
- Emulator: `C:\Users\space\Downloads\duckstation-windows-x64-release\duckstation-qt-x64-ReleaseLTCG.exe`, BIOS `bios\SCPH1001.BIN`

## PS1 memory card container (VERIFIED)
- 128 KiB = 16 blocks x 8192 B; block 0 = header/directory (64 frames x 128 B).
- Frame 0 magic `MC`. Frames 1..15 = directory entries.
- Directory entry: `u32 state` (0x51 first-link, 0x52 mid, 0x53 last, 0xA0 free),
  `u32 size_bytes`, `u16 next_block` (0xFFFF end), `char name[20]`.
- DexDrive `.gme`: strip the first 3,904 bytes (or seek to first `MC`).

## The DMW3 save (VERIFIED)
- ONE save, **4 blocks = 32,768 bytes**, occupying card blocks 1..4.
- Save names: USA `BASLUS-01436DMW3-USA`, EUR `BESLES-03936DMW3-EUR`.
  Region is identified by this string; the editor must handle both.
- Block 1 begins with the PS1 title frame: `SC`, then icon flags, then the
  title in **Shift-JIS full-width** ("Digimon World 3 Saved Data"), then the
  CLUT + icon bitmaps. Real game data starts at **0x0200** of the payload.
- Payload data extent: USA nonzero through 0x77FF; EUR only through 0x29C3
  (EUR is a much earlier save). Assume the live struct spans 0x0200-0x77FF.

## CRITICAL CAVEAT — do not repeat this mistake
The two samples are **different playthroughs**, not the same state dumped in two
regions. A USA-vs-EUR byte diff is a *progress* diff, NOT a region-layout map.
Never present diff regions as "region differences".

## Rules for every agent
1. Evidence or silence. Every claimed offset needs: offset, width, endianness
   (PS1 = little-endian, MIPS R3000A), observed value, and how you confirmed it.
2. Mark every finding CONFIRMED / PROBABLE / SPECULATIVE. Never dress up a guess.
3. Never write to `samples\`. Copy to `work\` if you need to mutate.
4. Never run unknown/old installer EXEs. Extraction only.
5. Write results as files in `research\` — the orchestrator reads files, not prose.
6. If blocked, report the blocker honestly. Fabricated data is the one
   unforgivable failure. A partial honest map beats a complete invented one.
