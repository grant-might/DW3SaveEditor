"""Launch the DMW3 Save Editor."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dmw3editor.ui.main_window import main

if __name__ == "__main__":
    raise SystemExit(main())
