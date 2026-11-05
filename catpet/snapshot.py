"""Headless rendering of every state into PNG files (``python -m catpet --snapshot``).

Output (in ``out/`` by default):

* ``<state>_<n>.png``  -- the raw, transparent frames as rendered by the widget
* ``strip_<state>.png`` -- the frames side by side, composited on a checkerboard
  (transparent pixels show the checkerboard; an opaque background would hide it)
* ``contact_sheet.png`` -- all strips under each other, on checkerboard and on solid colour
* ``timeline.txt`` -- state changes of a seeded 3 minute simulation with a scripted cursor
"""

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from .app import create_cat, get_app, load_sheet
from .brain import LEFT, RIGHT, State

GAP = 4

# (file name, state, facing)
SHOTS = [
    ("sit", State.SIT, RIGHT),
    ("blink", State.BLINK, RIGHT),
    ("sleep", State.SLEEP, RIGHT),
    ("walk_right", State.WALK, RIGHT),
    ("walk_left", State.WALK, LEFT),
    ("chase_left", State.CHASE, LEFT),
]


def checkerboard(w: int, h: int, cell: int = 12) -> QImage:
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    a, b = QColor(255, 0, 255), QColor(255, 190, 255)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            p.fillRect(x, y, cell, cell, a if (x // cell + y // cell) % 2 == 0 else b)
    p.end()
    return img


def strip(frames: list[QImage], background: QImage | QColor) -> QImage:
    fw, fh = frames[0].width(), frames[0].height()
    w = len(frames) * (fw + GAP) + GAP
    h = fh + 2 * GAP
    if isinstance(background, QColor):
        out = QImage(w, h, QImage.Format.Format_ARGB32)
        out.fill(background)
    else:
        out = background.copy(0, 0, w, h)
    p = QPainter(out)
    for i, f in enumerate(frames):
        p.drawImage(GAP + i * (fw + GAP), GAP, f)
    p.end()
    return out


def capture_state(cat, state: State, facing: int, count: int | None = None) -> list[QImage]:
    brain = cat.brain
    brain.force_state(state, facing)
    spec = brain.animator.spec
    frames = []
    for _ in range(count or spec.frames):
        frames.append(cat.render_image())
        brain.animator.advance(1.0 / spec.fps)  # step the animation only, not the behaviour
    return frames


def simulate_timeline(cat, seconds: float = 240.0, dt: float = 1 / 30) -> list[str]:
    """Run the real state machine with a scripted cursor; return the state changes.

    Script: at t=40 s the cursor stops 150 px right of the cat for 4 s (the cat should
    walk over and sit down); 5 s after the cat first falls asleep the cursor hovers
    over it for 1 s (the cat should wake up and sit).
    """
    brain = cat.brain
    brain.force_state(State.SIT)
    lines, last, t = [], None, 0.0
    hover = None  # (cursor position, until)
    slept_at = None
    woken = False
    while t < seconds:
        if hover is None and 40 <= t < 41:
            cx, cy = brain.center
            hover = ((cx + 150, cy - 30), t + 4)
            lines.append(f"{t:7.2f}s  -- cursor appears 150 px right of the cat")
        if brain.state is State.SLEEP and slept_at is None:
            slept_at = t
        if slept_at is not None and not woken and t >= slept_at + 5:
            woken = True
            hover = ((brain.center[0], brain.center[1] - 40), t + 1)
            lines.append(f"{t:7.2f}s  -- cursor hovers over the sleeping cat")
        cursor = None
        if hover is not None:
            if t < hover[1]:
                cursor = hover[0]
            else:
                hover = (None, -1)
        brain.update(dt, cursor)
        cur = (brain.state.value, brain.facing)
        if cur != last:
            facing = "right" if brain.facing > 0 else "left"
            lines.append(f"{t:7.2f}s  {brain.state.value:<6} facing={facing:<5} x={brain.x:7.1f}")
            last = cur
        t += dt
    return lines


def run(out_dir: Path) -> int:
    app = get_app()
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = load_sheet()
    cat = create_cat(sheet, rng=random.Random(42), cursor_pos=lambda: QPoint(-10_000, -10_000))
    cat.attach_to_primary_screen()

    strips_checker, strips_solid = [], []
    fw, fh = sheet.size
    max_frames = max(s.frames for s in sheet.meta.animations.values())
    bg = checkerboard(max_frames * (fw + GAP) + GAP, fh + 2 * GAP)
    for name, state, facing in SHOTS:
        frames = capture_state(cat, state, facing)
        for i, f in enumerate(frames):
            f.save(str(out_dir / f"{name}_{i}.png"))
        s = strip(frames, bg)
        s.save(str(out_dir / f"strip_{name}.png"))
        strips_checker.append(s)
        strips_solid.append(strip(frames, QColor(40, 60, 90)))

    col_w = bg.width()
    sheet_img = QImage(col_w * 2 + GAP, len(SHOTS) * bg.height(), QImage.Format.Format_ARGB32)
    sheet_img.fill(Qt.GlobalColor.white)
    p = QPainter(sheet_img)
    for row, (a, b) in enumerate(zip(strips_checker, strips_solid)):
        p.drawImage(0, row * bg.height(), a)
        p.drawImage(col_w + GAP, row * bg.height(), b)
    p.end()
    sheet_img.save(str(out_dir / "contact_sheet.png"))

    timeline = simulate_timeline(cat)
    (out_dir / "timeline.txt").write_text("\n".join(timeline) + "\n", encoding="utf-8")
    print(f"snapshot written to {out_dir.resolve()} "
          f"({len(SHOTS)} states, platform={app.platformName()!r})")
    return 0
