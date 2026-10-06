# Digimon World 3 Save Editor v0.1.0

The first public release of the DMW3 save editor for Windows.

## What is this

A desktop tool that edits Digimon World 3 (PlayStation 1) memory card saves. It supports USA and EUR saves and reads `.mcr`, `.mcd`, `.mc`, `.bin`, `.gme` (DexDrive), `.vgs`, and `.vmp` card images.

## Features

- Party Digimon for save slots 1 to 3, levels 1 to 99
- Partner Digimon
- Bits, capped at 9,999,999
- Play time (hours, minutes, seconds)
- Item inventory with art thumbnails and search (Items, Weapons, Armor, Accessories)
- All 35 card booster packs
- 48 important item flags
- Per-Digimon stats for the 8 roster partners
- Full digivolution trees with earned flags and DV levels; techniques are written so moves show up in game
- Complete 314 card collection with card art
- Field locator diff tool and a read-only hex view
- Five built in color themes

## Safety

- Nothing is written until you press Save
- The original file is backed up to a `.bak` on first save
- Only fields verified against real saves are editable; unknown regions are never written

## Download

Grab `DMW3SaveEditor-windows-x64.zip`, extract it anywhere, and run `DMW3SaveEditor.exe`. No install needed. Windows SmartScreen may prompt on first run because the app is not code signed.

Full details and screenshots are on the repository front page.
