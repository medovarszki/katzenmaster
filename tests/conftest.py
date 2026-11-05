import os
import sys
from pathlib import Path

# Headless Qt for every test; must be set before any Qt GUI import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app


@pytest.fixture(scope="session")
def meta():
    from katzenmaster import config
    from katzenmaster.sprites import load_meta

    return load_meta(config.SPRITE_JSON)


@pytest.fixture(scope="session")
def sheet(meta):
    from katzenmaster import config
    from katzenmaster.sprites import SpriteSheet

    return SpriteSheet(config.SPRITE_PNG, meta, config.SCALE)
