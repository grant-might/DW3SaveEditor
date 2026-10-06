# READ ME FIRST — every agent, no exceptions
> **STATUS: HISTORICAL — SUPERSEDED.** Wave-1 agent brief from the RE phase.
> The project has shipped (v0.1.0). For current project state read
> `SAVE_FORMAT.md`, `USAGE.md`, and `OPEN_LEADS.md`. Agent conventions now
> live in the dmw3-port-ops skill, not this file.

1. Read `docs/GROUND_TRUTH.md` then `docs/ADDENDUM_V2.md`. **ADDENDUM_V2 WINS**
   where they disagree — it corrects a wrong assumption in the original brief.

2. **SHELL PATH QUIRK (bites everyone):** your `terminal` runs bash/MSYS on
   Windows and **eats unquoted backslashes**. `D:\AGENT\x` becomes `D:AGENTx`.
   Always use FORWARD SLASHES for native programs:
   - Interpreter: `D:/AGENT/DMW3SaveEditor/.venv/Scripts/python.exe`
   - or quote it: `"D:\AGENT\DMW3SaveEditor\.venv\Scripts\python.exe"`
   Bare `python` / `python3` DO NOT EXIST on this host. Use the venv interpreter.
   It has PySide6 6.11.2, numpy 2.5.2, pytest.

3. Project root `D:/AGENT/DMW3SaveEditor`. Write deliverables to `research/`.
   `samples/` is READ-ONLY — copy to `work/` to mutate. Never touch `samples/`.

4. **Evidence or silence.** Every offset needs: offset (as `slot_base+0xNN`),
   width, endianness, observed value, and how you confirmed it. Label everything
   **CONFIRMED / PROBABLE / SPECULATIVE**.

5. **Fabrication is the only unforgivable failure.** A short honest result beats
   a long invented one. If you are blocked, say so plainly and say why. Do not
   invent offsets, IDs, cheat codes, file names, or test output. If you claim a
   test passes, paste the real pytest output.

6. Never run unknown/old installer EXEs. Extraction only.

## Already CONFIRMED by the orchestrator — do not re-derive, do not contradict
- Payload = 32,768 B, extracted from card blocks 1..4.
- **THREE in-game save slots**, 0x2700 each, at payload **0x0200 / 0x2900 / 0x5000**
  (repeat period 0x2700 @ 98.1% match; slots differ in only ~155/9984 bytes).
- `DMW3` ASCII tag at `slot_base+0x04`; slot header starts `E8 00 03 00`.
- **Active party = 3 records, stride 0x44 (68 B), at `slot_base+0x08`**
  (payload 0x208 / 0x24C / 0x290), found via repeated signature
  `13 40 2B 01 01 0D 0D 00` at exact 0x44 spacing.
- An HP `current <= max` u16-pair scan over the whole payload found **NOTHING**.
  Do NOT assume stored HP/MP pairs exist. Test, don't assume.
