"""Path resolution that works in BOTH the dev tree and a PyInstaller build.

PyInstaller (--onedir) places bundled data under sys._MEIPASS and keeps the
package at <bundle>/dmw3editor/. In the dev tree everything lives next to this
file. Call sites (assets, save data tables, logo, tick icons) use the
resolvers below so a frozen build finds the same files.
"""
from __future__ import annotations

import pathlib
import sys

_PKG = "dmw3editor"


def _bundle_root() -> pathlib.Path:
    """Top of the app bundle: _MEIPASS when frozen, project root otherwise."""
    if getattr(sys, "frozen", False):  # PyInstaller sets sys.frozen
        return pathlib.Path(sys._MEIPASS)  # noqa: SLF001
    return pathlib.Path(__file__).resolve().parent.parent


def pkg_dir() -> pathlib.Path:
    """The dmw3editor package directory (data assets live under it)."""
    return _bundle_root() / _PKG


def repo_root() -> pathlib.Path:
    """Bundle root / repo root (logo.png lives here in both layouts)."""
    return _bundle_root()


def writable_dir(rel: str) -> pathlib.Path:
    """A directory the app may WRITE at runtime (generated tick icons, caches).

    In the dev tree this is inside the package (so screenshots/QA see the same
    files); in a frozen build the bundle may be read-only (Program Files), so
    use the per-user local app data dir instead.
    """
    if getattr(sys, "frozen", False):
        base = pathlib.Path.home() / "AppData" / "Local" / "DMW3SaveEditor"
    else:
        base = pkg_dir()
    p = base / rel
    p.mkdir(parents=True, exist_ok=True)
    return p
