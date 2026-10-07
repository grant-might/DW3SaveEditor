# Digimon World 3 Save Editor v0.1.2

This release makes party swaps take effect in game, on both USA and PAL saves.

## Fix

A party member is stored twice in a save. The info summary holds partner ids, the values the load screen shows. The GameSave data section holds partner indices, and that is the copy the game loads. Earlier versions updated the summary only, so a swap was visible in the editor but the game still loaded the old team.

The editor now writes both copies, converting between the two value spaces with the region's party minimum, so the team shown in the editor is the team the game loads. This affects USA (`BASLUS-01436`) and PAL (`BESLES-03936`) saves alike.

The data-section copy is skipped for in-game slots 2 and 3, whose data sections sit in the range the editor does not write yet. Editing slot 1 works as before.

## Docs

`docs/MEMCARD_FORMAT.md` and `docs/SAVE_FORMAT.md` describe the two party copies and their value spaces, and the info header fields as the game writes them.

## Download

Grab `DMW3SaveEditor-windows-x64.zip`, extract it anywhere, and run `DMW3SaveEditor.exe`. No install needed. Windows SmartScreen may prompt on first run because the app is not code signed.
