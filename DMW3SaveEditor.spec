# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Digimon World 3 Save Editor.

Build:  ./.venv/Scripts/pyinstaller.exe DMW3SaveEditor.spec --noconfirm
Output: dist/DMW3SaveEditor/DMW3SaveEditor.exe  (onedir, portable)

Bundled layout mirrors the dev tree:
  _internal/dmw3editor/{assets,data}/...   (data files)
  _internal/logo.png                        (repo_root()/logo.png in frozen mode)
Frozen path resolver: dmw3editor/paths.py (sys._MEIPASS aware).
"""

block_cipher = None

a = Analysis(
    ["dmw3_save_editor.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("dmw3editor/assets", "dmw3editor/assets"),
        ("dmw3editor/data", "dmw3editor/data"),
        ("logo.png", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tests", "research"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DMW3SaveEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # GUI app: no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["logo.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DMW3SaveEditor",
)
