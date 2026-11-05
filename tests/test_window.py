import random

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QSystemTrayIcon

from catpet import config
from catpet.app import create_cat, warn_about_platform
from catpet.brain import LEFT, RIGHT, State
from catpet.tray import QUIT_TEXT, CatTray
from catpet.window import WINDOW_ATTRIBUTES, CatWindow


@pytest.fixture
def cat(qapp, sheet):
    w = create_cat(sheet, rng=random.Random(1), cursor_pos=lambda: QPoint(-10_000, -10_000))
    yield w
    w.stop()
    w.close()
    w.deleteLater()


@pytest.mark.parametrize("flag", [
    Qt.WindowType.FramelessWindowHint,
    Qt.WindowType.WindowStaysOnTopHint,
    Qt.WindowType.Tool,
    Qt.WindowType.WindowTransparentForInput,
    Qt.WindowType.WindowDoesNotAcceptFocus,
])
def test_window_flags(cat, flag):
    assert cat.windowFlags() & flag == flag


def test_tool_window_type(cat):
    # Qt.Tool is a window *type* (not in taskbar / Alt-Tab), not merely a flag bit
    assert cat.windowType() == Qt.WindowType.Tool
    assert cat.isWindow()


@pytest.mark.parametrize("attr", [
    Qt.WidgetAttribute.WA_TranslucentBackground,
    Qt.WidgetAttribute.WA_TransparentForMouseEvents,
    Qt.WidgetAttribute.WA_ShowWithoutActivating,
])
def test_window_attributes(cat, attr):
    assert attr in WINDOW_ATTRIBUTES
    assert cat.testAttribute(attr)


def test_flags_survive_show(cat):
    cat.start()
    flags = cat.windowHandle().flags()
    for f in (Qt.WindowType.FramelessWindowHint, Qt.WindowType.WindowStaysOnTopHint,
              Qt.WindowType.WindowTransparentForInput):
        assert flags & f == f
    assert cat.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_window_size_matches_scaled_sprite(cat):
    assert (cat.width(), cat.height()) == (32 * config.SCALE, 32 * config.SCALE)


def test_window_sits_on_bottom_of_available_geometry(qapp, cat):
    cat.attach_to_primary_screen()
    g = qapp.primaryScreen().availableGeometry()
    cat.start()
    assert cat.y() + cat.height() == g.y() + g.height()
    assert g.x() <= cat.x() <= g.x() + g.width() - cat.width()


def test_render_is_transparent_around_the_cat(cat):
    img = cat.render_image()
    assert img.size() == cat.size()
    for x, y in [(0, 0), (img.width() - 1, 0), (0, img.height() // 2)]:
        assert img.pixelColor(x, y).alpha() == 0
    opaque = sum(img.pixelColor(x, y).alpha() == 255
                 for y in range(0, img.height(), 3) for x in range(0, img.width(), 3))
    assert opaque > 100


def test_render_matches_sprite_frame(cat, sheet):
    for state, facing in [(State.SIT, RIGHT), (State.WALK, LEFT), (State.SLEEP, RIGHT)]:
        cat.brain.force_state(state, facing)
        expected = sheet.frame(cat.brain.animation, 0, cat.brain.mirrored).convertToFormat(
            QImage.Format.Format_ARGB32)
        assert cat.render_image() == expected


def test_tick_moves_window_with_brain(qapp, cat):
    cat.attach_to_primary_screen()
    cat.start()
    cat.brain.force_state(State.WALK, RIGHT)
    cat.brain.x = cat.brain.min_x + 10
    x0 = cat.brain.x
    cat._clock.restart()
    for _ in range(5):
        qapp.processEvents()
        cat.brain.update(0.05)
        cat._sync_position()
    assert cat.brain.x > x0
    assert cat.x() == round(cat.brain.x)


def test_tick_reads_cursor(qapp, sheet):
    calls = []

    def fake_cursor():
        calls.append(1)
        return QPoint(0, 0)

    w = create_cat(sheet, rng=random.Random(1), cursor_pos=fake_cursor)
    w.tick()
    assert calls
    w.close()


def test_default_cursor_source_is_qcursor(sheet):
    from PySide6.QtGui import QCursor
    import inspect

    sig = inspect.signature(CatWindow.__init__)
    assert sig.parameters["cursor_pos"].default is QCursor.pos


def test_tray_has_single_quit_action(qapp, sheet):
    tray = CatTray(qapp, sheet)
    actions = tray.menu.actions()
    assert [a.text() for a in actions] == [QUIT_TEXT] == ["Kilépés"]
    assert tray.icon.contextMenu() is tray.menu
    assert not tray.icon.icon().isNull()
    sizes = {(sz.width(), sz.height()) for sz in tray.icon.icon().availableSizes()}
    assert {(32, 32), (64, 64), (96, 96)} <= sizes


def test_tray_quit_action_quits(qapp, sheet, monkeypatch):
    called = []
    tray = CatTray.__new__(CatTray)
    monkeypatch.setattr(type(qapp), "quit", lambda *a: called.append(True))
    CatTray.__init__(tray, qapp, sheet)
    tray.quit_action.trigger()
    assert called


def test_tray_warns_when_unavailable(qapp, sheet, caplog, monkeypatch):
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", staticmethod(lambda: False))
    with caplog.at_level("WARNING"):
        CatTray(qapp, sheet)
    assert "no system tray" in caplog.text


@pytest.mark.parametrize("platform, warns", [("wayland", True), ("wayland-egl", True),
                                             ("xcb", False), ("windows", False)])
def test_wayland_warning(caplog, platform, warns):
    with caplog.at_level("WARNING"):
        warn_about_platform(platform)
    assert ("Wayland" in caplog.text) == warns
