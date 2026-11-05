"""Application wiring: QApplication, sprite sheet, brain, window and tray."""

from __future__ import annotations

import logging
import random
import signal
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from . import config
from .brain import CatBrain, ground_position
from .sprites import SpriteSheet, load_meta
from .tray import CatTray
from .window import CatWindow, screen_rect

log = logging.getLogger(__name__)


def load_sheet(scale: int = config.SCALE) -> SpriteSheet:
    return SpriteSheet(config.SPRITE_PNG, load_meta(config.SPRITE_JSON), scale)


def create_cat(sheet: SpriteSheet, rng: random.Random | None = None, cursor_pos=None) -> CatWindow:
    screen = QGuiApplication.primaryScreen()
    rect = screen_rect(screen) if screen is not None else (0, 0, 800, 600)
    brain = CatBrain(sheet.meta.animations, sheet.size, ground_position(rect, sheet.size), rng)
    if cursor_pos is None:
        return CatWindow(sheet, brain)
    return CatWindow(sheet, brain, cursor_pos)


def warn_about_platform(platform: str) -> None:
    if platform.startswith("wayland"):
        log.warning(
            "running on Wayland: the compositor may ignore window positioning and "
            "always-on-top, and the global cursor position is usually not available, "
            "so the cat may not sit on the taskbar edge or react to the cursor. "
            "Workaround: start with QT_QPA_PLATFORM=xcb (XWayland). See README."
        )


def get_app() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("catpet")
    app.setQuitOnLastWindowClosed(False)  # the window is a Tool window; quit via tray only
    return app


def run() -> int:
    app = get_app()
    warn_about_platform(app.platformName())
    sheet = load_sheet()
    cat = create_cat(sheet)
    cat.attach_to_primary_screen()
    tray = CatTray(app, sheet.frame("sit", 0))
    tray.show()
    cat.start()
    # Ctrl+C in the terminal also quits (the 30 fps timer lets Python handle the signal)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    log.info("catpet running on platform %r", app.platformName())
    return app.exec()
