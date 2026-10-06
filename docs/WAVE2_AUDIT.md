# Wave-2 agent audit — orchestrator verdict (2026-08-30)
> **STATUS: HISTORICAL — SUPERSEDED.** Audit verdicts from the wave-2 run.
> Every "REJECTED / do not wire into the editor" item in this file was later
> resolved by the controlled-diff campaign (items, cards, stats, DV) and is
> now shipped. Kept for history only.

The 5 Wave-2 research agents returned. Agent self-reports are NOT verification.
I audited every "found it" claim against the real sample bytes. Verdicts:

## TASK 1 — item inventory @ 0x1e47  → REJECTED (not a verified find)
- Script claims "fixed array @ 0x1e47, u16 LE x403".
- Payload base is 0x0200, so payload-relative 0x1e47 = CARD OFFSET 0x2047.
  That is inside the verified save-header / party-summary region (party records
  start at card 0x0208). An item inventory cannot live there.
- Decoded `count`/`flags` columns are internally inconsistent (Balanced Pack
  count=32 flags=184) and the read is a heuristic stride decode, not a flat
  id-indexed array.
- Consistent with the earlier exhaustive search: 1117 statistically
  indistinguishable id-indexed inventory candidates; this is one of them, not
  confirmed.

## TASK 2 — per-Digimon stat/XP SoA @ 0x03A7, stride 44  → PLAUSIBLE, LOW CONF
- A repeating u8[44]-stride table of 44 Digimon does exist there (field 0 =
  level, matches the party: 98/99/99 lockstep on USA).
- Semantic mapping of fields f1..f39 to specific profile members is UNRESOLVED
  (agent's own "LOW confidence"). Do NOT wire into editor until a controlled
  diff confirms field meaning.

## TASK 3 — card collection @ 0x2E00  → REJECTED (not a verified find)
- 0x2E00 payload = card 0x3000, inside the UNIDENTIFIED 0x2900-0x7700 region
  the editor refuses to write.
- Internal contradiction flagged by the agent itself: EUR "0/314 owned (empty)"
  vs "secondary dex EUR 314/314 MAXED" — cannot both hold. Dense/sparse
  asymmetry is the right signal but unconfirmed without a controlled in-game
  diff.

## TASK 4 — adversarial tests  → agent hit max_iterations (truncated)
- Already covered: I wrote tests/test_adversarial.py earlier and FIXED the 2
  real bugs it surfaced (negative-slot silent write; corrupt-dir struct.error).
- No action needed; suite is green.

## TASK 5 — docs/packaging  → ACCEPTED
- README, USAGE, requirements, pyproject, .gitignore all present and the
  documented commands were verified by the agent (pytest green).

## CONSEQUENCE FOR THE EDITOR
- Items, card collection, and per-Digimon stat blocks remain UNEXPOSED.
- The Field Locator tab (controlled-diff) stays the only path to confirm them.
- dmw3editor/core/save.py MUST keep refusing writes to 0x2900-0x7700.
- tests/test_adversarial.py asserts this refusal — keep it.
