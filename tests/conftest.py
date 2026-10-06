"""Shared pytest configuration.

The DMW3 editor's GUI tests drive real Qt widgets. They run on the system's
native Qt platform (the app is a desktop GUI). Forcing the "offscreen" backend
is NOT done here: on this Windows host the offscreen/ANGLE backend corrupts the
process when mixed with the numpy-heavy core tests, whereas the native backend
renders correctly (see work/shots/*.png). Headless CI can set
QT_QPA_PLATFORM=offscreen per-run if a display is unavailable.
"""

import pytest


@pytest.fixture(scope="session")
def qapp():
    """One QApplication for the whole test session (pytest-qt manages it)."""
    from PySide6.QtWidgets import QApplication

    from dmw3editor.ui import theme

    app = QApplication.instance() or QApplication(["dmw3-editor-test"])
    theme.apply(app)
    yield app


@pytest.fixture(scope="session")
def app(qapp):
    """Alias used by the GUI tests."""
    return qapp
