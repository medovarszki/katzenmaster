"""Render the README picture: the sitting cat on a simple desktop with a taskbar.

    python docs/make_screenshot.py          # writes docs/screenshot.png

The cat is drawn by the real window (``CatWindow.render_image``, i.e. its paintEvent);
only the wallpaper and the taskbar are painted here. Everything is rendered at 2x so
the picture stays crisp on HiDPI screens (the README shows it at half size).
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter  # noqa: E402

from katzenmaster import config  # noqa: E402
from katzenmaster.app import create_cat, get_app, load_sheet  # noqa: E402
from katzenmaster.brain import RIGHT, State  # noqa: E402

DPR = 2  # device pixel ratio of the picture
WIDTH, HEIGHT = 480, 200  # logical size
TASKBAR = 40  # logical height
CAT_X = 300  # logical x of the cat's left edge
OUT = ROOT / "docs" / "screenshot.png"


def render(out: Path = OUT) -> Path:
    get_app()
    w, h, bar = WIDTH * DPR, HEIGHT * DPR, TASKBAR * DPR
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    p = QPainter(img)

    # wallpaper: a soft evening sky
    sky = QLinearGradient(0, 0, 0, h - bar)
    sky.setColorAt(0.0, QColor(58, 84, 140))
    sky.setColorAt(1.0, QColor(170, 190, 225))
    p.fillRect(0, 0, w, h - bar, sky)

    # a neutral taskbar with a few app buttons on the left
    p.fillRect(0, h - bar, w, bar, QColor(32, 36, 46))
    p.fillRect(0, h - bar, w, DPR, QColor(70, 76, 92))
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)
    for i, color in enumerate((QColor(96, 130, 200), QColor(110, 170, 120), QColor(205, 150, 90))):
        p.setBrush(color)
        p.drawRoundedRect(QRectF((12 + i * 36) * DPR, h - bar + 8 * DPR, 24 * DPR, 24 * DPR),
                          5 * DPR, 5 * DPR)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # the tray icon: the same sitting-cat image the app puts into the system tray
    tray_sheet = load_sheet(scale=1)
    icon = tray_sheet.frame("sit", 0, scale=DPR // 2 if DPR >= 2 else 1)
    p.drawImage(w - (16 + 12) * DPR, h - bar + 12 * DPR, icon)

    # the cat, rendered by the real window, standing on the taskbar
    sheet = load_sheet(scale=config.SCALE * DPR)
    cat = create_cat(sheet, rng=random.Random(1), cursor_pos=lambda: QPoint(-10_000, -10_000))
    cat.brain.force_state(State.SIT, RIGHT)
    frame = cat.render_image()
    p.drawImage(CAT_X * DPR, h - bar - frame.height(), frame)
    p.end()

    img.setDevicePixelRatio(DPR)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not img.save(str(out)):
        raise SystemExit(f"could not write {out}")
    return out


if __name__ == "__main__":
    print(f"wrote {render()}")
