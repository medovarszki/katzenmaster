"""The transparent, click-through, always-on-top window that shows the cat."""

from __future__ import annotations

import logging

from PySide6.QtCore import QElapsedTimer, QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QImage, QPainter, QRegion
from PySide6.QtWidgets import QWidget

from . import config
from .brain import CatBrain, ground_position
from .sprites import SpriteSheet

log = logging.getLogger(__name__)

WINDOW_FLAGS = (
    Qt.WindowType.FramelessWindowHint  # no title bar / border
    | Qt.WindowType.WindowStaysOnTopHint  # always on top
    | Qt.WindowType.Tool  # not in taskbar / Alt-Tab (WS_EX_TOOLWINDOW, _NET_WM_WINDOW_TYPE_UTILITY)
    | Qt.WindowType.WindowTransparentForInput  # click-through (WS_EX_TRANSPARENT, X11 empty input shape)
    | Qt.WindowType.WindowDoesNotAcceptFocus  # never steals keyboard focus
    | Qt.WindowType.NoDropShadowWindowHint  # no shadow around the transparent window
)

WINDOW_ATTRIBUTES = (
    Qt.WidgetAttribute.WA_TranslucentBackground,
    Qt.WidgetAttribute.WA_TransparentForMouseEvents,
    Qt.WidgetAttribute.WA_ShowWithoutActivating,
    Qt.WidgetAttribute.WA_NoSystemBackground,
)


def screen_rect(screen) -> tuple[int, int, int, int]:
    g = screen.availableGeometry()
    return (g.x(), g.y(), g.width(), g.height())


class CatWindow(QWidget):
    def __init__(self, sheet: SpriteSheet, brain: CatBrain, cursor_pos=QCursor.pos) -> None:
        super().__init__(None, WINDOW_FLAGS)
        for attr in WINDOW_ATTRIBUTES:
            self.setAttribute(attr, True)
        self.setWindowTitle("katzenmaster")
        self.sheet = sheet
        self.brain = brain
        self._cursor_pos = cursor_pos
        self.setFixedSize(*sheet.size)
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(config.TICK_MS)
        self._timer.timeout.connect(self.tick)
        self._screen = None
        self._last_frame_key = None

    # ------------------------------------------------------------ screen handling
    def attach_to_primary_screen(self) -> None:
        app = QGuiApplication.instance()
        app.primaryScreenChanged.connect(self._on_primary_screen_changed)
        self._on_primary_screen_changed(QGuiApplication.primaryScreen())

    def _on_primary_screen_changed(self, screen) -> None:
        if screen is None:
            log.warning("no primary screen available")
            return
        if self._screen is not None:
            try:
                self._screen.availableGeometryChanged.disconnect(self._on_geometry_changed)
            except (RuntimeError, TypeError):
                pass
        self._screen = screen
        screen.availableGeometryChanged.connect(self._on_geometry_changed)
        self._on_geometry_changed()

    def _on_geometry_changed(self, *_args) -> None:
        rect = screen_rect(self._screen)
        self.brain.set_ground(ground_position(rect, self.sheet.size))
        log.info("available geometry %s -> walking range x=%d..%d, y=%d",
                 rect, self.brain.min_x, self.brain.max_x, self.brain.y)
        self._sync_position()

    # ------------------------------------------------------------------ main loop
    def start(self) -> None:
        self._sync_position()
        self.show()
        self._clock.start()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def tick(self) -> None:
        dt = self._clock.restart() / 1000.0
        p = self._cursor_pos()
        self.brain.update(dt, (p.x(), p.y()))
        self._sync_position()
        key = (self.brain.animation, self.brain.frame, self.brain.mirrored)
        if key != self._last_frame_key:
            self._last_frame_key = key
            self.update()

    def _sync_position(self) -> None:
        x, y = self.brain.position
        if (self.x(), self.y()) != (x, y):
            self.move(x, y)

    # ------------------------------------------------------------------ painting
    def current_image(self) -> QImage:
        b = self.brain
        return self.sheet.frame(b.animation, b.frame, b.mirrored)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), QColor(0, 0, 0, 0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.drawImage(0, 0, self.current_image())
        p.end()

    def render_image(self) -> QImage:
        """Render the widget through its own paintEvent into a transparent ARGB image."""
        img = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        self.render(img, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
        return img.convertToFormat(QImage.Format.Format_ARGB32)
