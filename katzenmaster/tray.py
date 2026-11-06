"""System tray icon with a single "Kilépés" (quit) entry -- the only UI."""

from __future__ import annotations

import logging

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import __version__
from .sprites import SpriteSheet

log = logging.getLogger(__name__)

QUIT_TEXT = "Kilépés"


def tray_icon(sheet: SpriteSheet) -> QIcon:
    """The sitting cat at 1x, 2x and 3x (nearest neighbour), so the OS can pick a crisp size."""
    icon = QIcon()
    for scale in (1, 2, 3):
        icon.addPixmap(QPixmap.fromImage(sheet.frame("sit", 0, scale=scale)))
    return icon


class CatTray:
    def __init__(self, app: QApplication, sheet: SpriteSheet) -> None:
        self.menu = QMenu()
        self.quit_action = self.menu.addAction(QUIT_TEXT)
        self.quit_action.triggered.connect(app.quit)
        self.icon = QSystemTrayIcon(tray_icon(sheet), app)
        self.icon.setToolTip(f"katzenmaster {__version__}")
        self.icon.setContextMenu(self.menu)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("no system tray available: the quit menu will not be visible; "
                        "stop the app with Ctrl+C in the terminal or by killing the process")

    def show(self) -> None:
        self.icon.show()
