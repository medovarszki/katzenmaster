"""System tray icon with a single "Kilépés" (quit) entry -- the only UI."""

from __future__ import annotations

import logging

from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

log = logging.getLogger(__name__)

QUIT_TEXT = "Kilépés"


class CatTray:
    def __init__(self, app: QApplication, icon_image: QImage) -> None:
        self.menu = QMenu()
        self.quit_action = self.menu.addAction(QUIT_TEXT)
        self.quit_action.triggered.connect(app.quit)
        self.icon = QSystemTrayIcon(QIcon(QPixmap.fromImage(icon_image)), app)
        self.icon.setToolTip("catpet")
        self.icon.setContextMenu(self.menu)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("no system tray available: the quit menu will not be visible; "
                        "stop the app with Ctrl+C in the terminal or by killing the process")

    def show(self) -> None:
        self.icon.show()
