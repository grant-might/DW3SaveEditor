# Using the Digimon World 3 Save Editor

This is a task-oriented walkthrough for the current shipped UI. Read
[README.md](../README.md) first for the supported formats and the safety rules.
Everything here matches the app as of v0.1.0.

The editor is read-mostly until you load a card: nothing is editable, and
nothing is written to disk, until you press **Save**.

---

## 1. Get your memory card out of DuckStation

DuckStation stores each PS1 memory card as a single file. Where it lives
depends on whether you installed DuckStation portably or as an installed app:

- **Portable install** (you unzipped it somewhere): `<DuckStation folder>/memcards/`
- **Installed app** (Windows): `Documents/DuckStation/memcards/` under your
  user profile.

Confirm the exact folder inside DuckStation: **Settings → Memory Cards**. The
slots list the file each slot maps to. Typical filenames are
`shared_card_1.mcd`, `slot_1.mcd`, `slot_2.mcd`, etc.

Copy that file somewhere you control — e.g. into the `work/` folder or your
Desktop. **Edit the copy, never the only copy.** The editor also writes a `.bak`
automatically, but your own copy is the real safety net.

> Other emulators (ePSXe, RetroArch/Beetle) and real hardware dumps all produce
> the same raw 128 KiB card image, so any `.mcr/.mcd/.mc/.bin` file works.
> `.gme`, `.vgs` and `.vmp` are read too. USA and EUR saves are supported.

---

## 2. The layout

After you open a card, the sidebar shows every page:

- **SAVE SLOTS** — Slot 1 / 2 / 3, one page per in-game save slot.
- **INVENTORY** — Items, Weapons, Armor, Accessories, Card Packs,
  Important Items.
- **PARTNERS & COLLECTION** — Digimon (per-Digimon stats for all 8 partners),
  Digivolution, Cards.
- **TOOLS** — Field Locator, Hex Editor.
- **APPEARANCE** — Themes.

The **status line** above the sidebar shows the detected region and whether
the header checksums are valid.

---

## 3. Edit a save slot (party, money, time)

1. Open your copied card file with **Open card…**.
   - If the card has no DMW3 save you'll get: *"No Digimon World 3 save found
     on this card…"* — use a card that actually has a DW3 save on it.
2. Pick the **Slot** page for the slot you want to change. An empty slot is
   labelled *"(empty)"* — don't edit an empty slot; the game may reject a save
   the editor fabricates there.
3. **Party:** use the **Digimon** dropdown for each of the three party members.
   Every entry shows the species name and id. Set the **Level** spinner
   (1–99) for that row, or press **Set all to Lv99**.
4. **Partner:** use the **Partner** dropdown in the Player box.
5. **Bits:** type a value up to the game cap, or press **Max** for 9,999,999.
6. **Play time:** set hours / minutes / seconds exactly (cosmetic only).
7. Click **Save** (or **Save as…** to write a new file and leave the original
   untouched). The first save to a path writes a `<name>.bak` next to it.

---

## 4. Inventory pages

- **Items / Weapons / Armor / Accessories:** a table of every slot the game
  stores, with its own art thumbnail and a search box. Select a row, set a
  quantity, then **Apply**, **Max**, or **Zero**.
- **Card Packs:** all 35 booster packs, quantities 0–99.
- **Important Items:** the 48 key-item flags in their in-game screen order.

---

## 5. Digimon, Digivolution, Cards

- **Digimon:** per-Digimon stats for all 8 base-rookie partners — level, EXP,
  current/max HP and MP, and the 13 stats.
- **Digivolution:** the digivolution tree for a selected Digimon. Tick a form
  as **earned** and set its DV level, or press **Max earned DV to 99** to do
  the whole tree. Setting a form's DV also writes the technique record, so the
  form actually knows its moves in-game.
- **Cards:** the full 314-card collection with art. Set copies 0–9 per card,
  or **Set all to 9**.

---

## 6. Field Locator and Hex Editor (read-only)

- **Field Locator:** compare two saves made at different points in the game
  and see exactly which bytes changed. It never writes.
- **Hex Editor:** a read-only hex view of the raw payload with the verified
  regions marked. Look, don't touch.

---

## 7. Restoring from a `.bak`

The editor never overwrites an existing `.bak`, and writes one only on the
first save to a given path. To roll back:

1. Find the backup next to the file you edited — same folder, same name with
   `.bak` appended. Example: if you saved `card.mcd`, the backup is
   `card.mcd.bak`.
2. Delete (or rename) the edited file, then rename `card.mcd.bak` back to
   `card.mcd`.
3. Reload it in the editor or emulator to confirm.

If you used **Save as…**, your original file was never touched — just open the
original instead.

---

## 8. Switching themes

Open the **Themes** page and pick one of the five palettes. The change applies
instantly, no restart, and sticks for the next launch.

---

## Safety checklist (read this every time)

- [ ] You edited a **copy** of the card, and you still have the original
      somewhere else.
- [ ] You did **not** edit an empty slot.
- [ ] You know the editor only touches proven fields; anything not proven is
      refused (see SAVE_FORMAT.md).
- [ ] After saving, you loaded the card in an emulator and confirmed the game
      boots and the slot loads before trusting it on real hardware.

## Running the tests (for contributors)

The suite must run in two isolated processes — Qt and numpy cannot share one
pytest process on this host. Use the bundled runner:

```bash
./.venv/Scripts/python.exe run_tests.py
```

Or manually, from the project root:

```bash
./.venv/Scripts/python.exe -m pytest tests/ -m "not gui" -q -p no:cacheprovider
QT_QPA_PLATFORM=windows ./.venv/Scripts/python.exe -m pytest \
  tests/test_gui.py tests/test_field_locator.py tests/test_collections_gui.py \
  -m gui -q -o addopts= -p no:cacheprovider
```

Expected green: **157 passed / 11 skipped** (core) and **24 passed /
17 skipped** (GUI), both exit 0.
