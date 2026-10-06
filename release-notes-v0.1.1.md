# Digimon World 3 Save Editor v0.1.1

This release fixes party decoding for USA saves.

## Fix

USA saves previously showed the wrong party in the editor, while EUR (PAL) saves read correctly. The two releases use different party id spaces and the editor was reading USA cards through the wrong one, so a team of Kumamon, Guilmon and Patamon displayed as Agumon, Patamon and an invalid id.

The party fields in both releases now use the same id space. A party member is partner id 3 through 10, which is Kotemon through Patamon, matching what the shared game code stores in the save. USA and EUR cards holding the same team now decode to the same party.

Nothing else changed. All other editing behaviour is the same as v0.1.0.

## Download

Grab `DMW3SaveEditor-windows-x64.zip`, extract it anywhere, and run `DMW3SaveEditor.exe`. No install needed. Windows SmartScreen may prompt on first run because the app is not code signed.
