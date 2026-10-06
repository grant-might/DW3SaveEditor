# Digimon World 3 Save Editor

Edit your Digimon World 3 (PlayStation 1) memory card saves from your PC. No console hacking, no cheat devices, no hex editing required. Open a card, change what you want, save, and load it back into your emulator or real memory card.

Works with **USA and EUR** saves. Loads `.mcr`, `.mcd`, `.mc`, `.bin`, `.gme` (DexDrive), `.vgs`, and `.vmp` card images. Every edit goes through a real checksum recompute, so the game reads the card as valid. A backup of your original file is created automatically before the first save, and nothing is written to disk until you press Save.

![The main slot editor with a save loaded. Shows party Digimon (Agumon, Veemon, Guilmon at Lv 99), the partner Agumon, 9,999,999 Bits, and play time, plus the save slots sidebar.](https://github.com/user-attachments/assets/6d5962a6-80d8-4be6-b55b-629deeeeee45)

## What it can do

### Save slots
- **Party Digimon.** Pick any of the 8 base rookies for slots 1 to 3 and set each level from 1 to 99. A one click "Set all to Lv99" button is there if you want it.
- **Partner.** Choose your partner Digimon.
- **Bits.** Set your in-game money, capped at the game's maximum of 9,999,999. A "Max" button fills it instantly.
- **Play time.** Set hours, minutes, and seconds exactly.

### Inventory
- **Items, Weapons, Armor, and Accessories.** Every slot the game stores, with its own art thumbnail. Search by name with the filter box. Select a row and apply a quantity, max it, or zero it. The full name list comes from the game data, so you see real names like Power Charge, not slot numbers.
- **Card Packs.** All 35 booster packs with quantities from 0 to 99.
- **Important Items.** The 48 key and important item flags in their in-game screen order.

![Item inventory with 48 of 48 items shown. Power Charge (59) is selected with quantity controls at the bottom.](https://github.com/user-attachments/assets/228b8d2e-1e44-41af-ac98-55705103fb26)

### Partners and collection
- **Digimon.** Per-Digimon stats for all 8 roster partners: HP, MP, level, EXP, and stats, verified byte exact against a live card.
- **Digivolution.** The full digivolution tree for each Digimon. Tick a form as earned and set its DV level, the in-game value used to unlock evolutions. When you set a form's DV, the technique record is written too, so the Digimon actually knows its moves in-game, not just on paper. A one click "Max earned DV to 99" handles the whole tree.
- **Cards.** The complete 314 card collection with card art. Set copies from 0 to 9 for every card, individually or all at once.

![Digivolution screen for Agumon. All forms (Greymon through Paildramon) show earned checkboxes and DV level 99, with the rookie sprite row on top.](https://github.com/user-attachments/assets/4edf189f-6560-4c8d-bbfb-21aeb77fe0cd)

![Card collection showing card art and copy counts. Sacred Spear (8 copies) is selected.](https://github.com/user-attachments/assets/b2ed7627-d182-4db2-8fca-3ab3a1819430)

### Tools
- **Field Locator.** A read-only tool that compares two saves made at different points in the game and shows exactly which bytes changed. This is how new fields get found and verified; it never writes to your card.
- **Hex Editor.** A full read-only hex view of the raw save with verified regions marked, for people who want to look under the hood.
- **Themes.** Five built in color themes, including a default Digimon blue with Agumon yellow accents. Switch live from the Themes page, no restart needed.

## What it will not do

This editor is deliberately honest about the limits of the reverse engineering. It only writes fields that have been proven against real saves, and it will not write to parts of the save that are not yet understood. If a field is not listed above, it means its location in the save has not been proven yet, and the editor will refuse to touch it rather than risk corrupting your save. When new fields are verified, they get added.

## Safety

- The editor never writes to your card until you click Save.
- The first time you overwrite a file, the original is copied to a `.bak` file right next to it. The editor never overwrites an existing `.bak`.
- Keep a clean copy of a fresh save around if you want a pure baseline, since the editor only touches a card once you open and edit it.
- After editing, load the card in an emulator and confirm the game boots and your slot loads before trusting it on real hardware. On DuckStation, the memory card is read at game boot, so fully restart the game between cards.

## Getting the app

Download the latest release from the **Releases** page on this repository. Grab the `.zip`, extract it anywhere, and run `DMW3SaveEditor.exe`. No Python, no dependencies, no install needed. Windows SmartScreen may ask you to confirm the first run because the app is not code signed; that is expected for an indie tool.

## Requirements

- Windows 10 or 11
- A Digimon World 3 (USA or EUR) save on a PS1 memory card image, or one exported from DuckStation, a DexDrive, or other PS1 save tools
- For real hardware use, a way to get the card back onto your memory card (a DexDrive, a memory card reader, or a USB adapter)

## Saving back to your card

1. Export the memory card from your emulator, or use the card file it already keeps.
2. Open that file here, make your edits, and Save.
3. Load the edited file back into the emulator, or copy it to your memory card hardware.

DuckStation users: the app can open the `.mcr` card file DuckStation keeps in its memcards folder directly.

## Running from source

The code is in `dmw3editor/`. With Python 3.10 or newer on Windows:

```
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
python dmw3_save_editor.py
```

The tests run with `python run_tests.py` or `pytest`, and use the card images in `samples/`.

## License

The full license is in [LICENSE.md](LICENSE.md). In short: use it, change it and share it for free for anything noncommercial, personal or educational. If you pass it on, send your changes back to this project first, and pass the same license on with it. Commercial use needs a paid license from the author, which you can ask about on this repository.

The source is published so you can read exactly what the app does to your save before trusting it with one.
