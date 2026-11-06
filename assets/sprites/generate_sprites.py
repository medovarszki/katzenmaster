"""Generate the pixel-art cat sprite sheet (sprites.png + sprites.json).

Run from anywhere:  python assets/sprites/generate_sprites.py

Layout: 32x32 cells, one animation per row (sit, blink, sleep, walk, stretch, yawn,
groom). The side-view animations (walk, stretch) face RIGHT; the app mirrors them
for facing left.
Only PySide6 (QImage) is used to write the PNG.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

CELL = 32

# palette (RGBA)
PALETTE = {
    "o": (43, 29, 22, 255),  # outline
    "b": (232, 145, 58, 255),  # body orange
    "s": (196, 106, 34, 255),  # stripes / far legs
    "w": (248, 222, 184, 255),  # cream (muzzle, chest, paws)
    "p": (240, 150, 170, 255),  # pink (nose, inner ear)
    "e": (30, 24, 20, 255),  # eye
    "h": (255, 255, 255, 255),  # eye highlight
    "z": (80, 120, 210, 255),  # sleep "z"
}

# (name, frames, fps, loop) in row order
ANIMATIONS = [
    ("sit", 4, 4, True),
    ("blink", 4, 12, False),
    ("sleep", 4, 2, True),
    ("walk", 6, 10, True),
    ("stretch", 6, 4, False),
    ("yawn", 6, 5, False),
    ("groom", 4, 4, True),
]

# animations drawn facing right (mirrored by the app when the cat faces left)
FACES_RIGHT = ("walk", "stretch")


class Grid:
    """A tiny 32x32 raster of palette keys (None = transparent)."""

    def __init__(self) -> None:
        self.px: list[list[str | None]] = [[None] * CELL for _ in range(CELL)]

    def set(self, x: int, y: int, c: str) -> None:
        if 0 <= x < CELL and 0 <= y < CELL:
            self.px[y][x] = c

    def get(self, x: int, y: int) -> str | None:
        if 0 <= x < CELL and 0 <= y < CELL:
            return self.px[y][x]
        return None

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: str) -> None:
        for y in range(CELL):
            for x in range(CELL):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, c)

    def rect(self, x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def triangle(self, a, b, c_, col: str) -> None:
        def sign(p, q, r):
            return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])

        for y in range(CELL):
            for x in range(CELL):
                p = (x, y)
                d1, d2, d3 = sign(p, a, b), sign(p, b, c_), sign(p, c_, a)
                neg = d1 < 0 or d2 < 0 or d3 < 0
                pos = d1 > 0 or d2 > 0 or d3 > 0
                if not (neg and pos):
                    self.set(x, y, col)

    def line(self, x0: float, y0: float, x1: float, y1: float, c: str, width: int = 1) -> None:
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            for dx in range(width):
                for dy in range(width):
                    self.set(x + dx, y + dy, c)

    def outline(self) -> None:
        """Add a 1px outline around all opaque pixels (4-neighbourhood)."""
        add = []
        for y in range(CELL):
            for x in range(CELL):
                if self.px[y][x] is None and any(
                    self.get(x + dx, y + dy) not in (None, "o")
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    add.append((x, y))
        for x, y in add:
            self.px[y][x] = "o"

    def draw_text(self, rows: list[str], x0: int, y0: int) -> None:
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.set(x0 + dx, y0 + dy, ch)


# --------------------------------------------------------------------------
# sitting cat (front view) -- used by "sit" and "blink"
# --------------------------------------------------------------------------

def sitting_cat(tail_phase: int, eyes: str, mouth: str = "closed", paw: int | None = None) -> Grid:
    """Front view. ``mouth``: closed / small / wide; ``paw``: lick phase of the raised paw."""
    g = Grid()
    # tail on the ground, curling up at the tip (drawn first, behind the body)
    tips = [(27, 22), (28, 23), (28, 25), (27, 24)]
    tx, ty = tips[tail_phase % len(tips)]
    g.line(19, 28, 24, 29, "b", width=2)
    g.line(24, 29, 27, 27, "b", width=2)
    g.line(27, 27, tx, ty, "b", width=2)
    g.rect(tx, ty, tx + 1, ty, "s")  # dark tail tip
    # body
    g.ellipse(15.5, 24.5, 7.0, 6.2, "b")
    # chest
    g.ellipse(15.5, 23.5, 3.0, 4.0, "w")
    # front paws
    if paw is None:
        g.rect(11, 29, 13, 30, "w")
    g.rect(18, 29, 20, 30, "w")
    # ears
    g.triangle((8, 13), (9, 4), (14, 9), "b")
    g.triangle((23, 13), (22, 4), (17, 9), "b")
    # head
    g.ellipse(15.5, 14.0, 7.6, 5.6, "b")
    # inner ears
    g.triangle((10, 10), (10, 6), (12, 9), "p")
    g.triangle((21, 10), (21, 6), (19, 9), "p")
    # muzzle
    g.ellipse(15.5, 17.0, 3.0, 1.6, "w")
    g.outline()
    # forehead stripes
    for x in (13, 15, 16, 18):
        g.set(x, 9, "s")
    g.set(15, 10, "s")
    g.set(16, 10, "s")
    # side stripes on body
    for y in (22, 25):
        g.set(9, y, "s")
        g.set(10, y, "s")
        g.set(21, y, "s")
        g.set(22, y, "s")
    # paw split
    if paw is None:
        g.set(12, 30, "o")
    g.set(19, 30, "o")
    # eyes
    for ex in (11, 19):
        if eyes == "open":
            g.rect(ex, 13, ex + 1, 14, "e")
            g.set(ex, 13, "h")
        elif eyes == "half":
            g.rect(ex, 14, ex + 1, 14, "e")
        else:  # closed
            g.set(ex, 14, "o")
            g.set(ex + 1, 14, "o")
            g.set(ex - 1 if ex < 15 else ex + 2, 13, "o")
    # nose + mouth
    g.set(15, 16, "p")
    g.set(16, 16, "p")
    if mouth == "small":
        g.draw_text(["oooo", "oeeo", ".oo."], 14, 17)
    elif mouth == "wide":
        g.draw_text(["oooooo", "oheeho", "oeppeo", "ooppoo", "..oo.."], 13, 17)
    else:
        g.set(15, 17, "o")
        g.set(16, 17, "o")
        g.set(14, 18, "o")
        g.set(17, 18, "o")
    if paw is not None:
        _raised_paw(g, paw)
    return g


def _raised_paw(g: Grid, phase: int) -> None:
    """Left front paw lifted to the mouth; ``phase`` alternates the licking stroke."""
    up = phase % 2
    # foreleg from the chest up to the face, outlined by hand (it overlaps the body)
    g.draw_text(
        [
            "..ooo",
            ".owwwo",
            ".owwwo",
            "obbbo",
            "obbbo",
            "obbbo",
            "obbbo",
            "obbbo",
            "obbbo",
            "obbbo",
            "obbbo",
            ".ooo",
        ],
        10, 15 - up,
    )
    # tongue reaching out to the paw
    if up == 0:
        g.set(15, 18, "p")
        g.set(15, 19, "p")


# --------------------------------------------------------------------------
# sleeping cat (side view, curled)
# --------------------------------------------------------------------------

Z_SMALL = ["zzz", ".z.", "zzz"]
Z_BIG = ["zzzz", "..z.", ".z..", "zzzz"]


def sleeping_cat(frame: int) -> Grid:
    g = Grid()
    breathe = 0.0 if frame % 2 == 0 else 0.6
    # body loaf
    g.ellipse(17.0, 25.5 - breathe / 2, 11.0, 4.6 + breathe / 2, "b")
    # head on the left, resting low
    g.triangle((4, 22), (5, 16), (9, 21), "b")
    g.triangle((9, 21), (11, 16), (13, 22), "b")
    g.ellipse(8.5, 25.0, 5.4, 4.2, "b")
    g.triangle((5, 20), (6, 18), (7, 20), "p")
    g.triangle((10, 20), (11, 18), (12, 21), "p")
    # tail wrapping round the front
    g.line(28, 27, 22, 29, "s", width=2)
    g.line(22, 29, 13, 29, "s", width=2)
    # muzzle / paw
    g.ellipse(6.5, 27.5, 2.2, 1.3, "w")
    g.outline()
    # stripes on the back
    for x in (15, 19, 23):
        g.set(x, 21 + (0 if frame % 2 == 0 else 0), "s")
        g.set(x, 22, "s")
    # closed eyes
    g.set(6, 25, "o")
    g.set(7, 25, "o")
    g.set(10, 25, "o")
    g.set(11, 25, "o")
    g.set(8, 27, "p")
    # z's floating up
    z_positions = [(16, 15, Z_SMALL), (18, 12, Z_SMALL), (20, 8, Z_BIG), (23, 4, Z_BIG)]
    for i in range(frame + 1):
        if frame - i < 2:  # show the current and previous z
            x, y, glyph = z_positions[i]
            g.draw_text(glyph, x, y)
    return g


# --------------------------------------------------------------------------
# walking cat (side view, facing right)
# --------------------------------------------------------------------------

def walking_cat(frame: int, frames: int) -> Grid:
    g = Grid()
    phase = 2 * math.pi * frame / frames
    bob = 1 if frame % 3 == 1 else 0

    def leg(x_base: float, offset: float, col: str) -> None:
        dx = round(2.0 * math.sin(phase + offset))
        lift = 1 if math.cos(phase + offset) > 0.5 else 0
        x = int(x_base + dx)
        g.rect(x, 24, x + 1, 29 - lift, col)
        g.rect(x, 30 - lift, x + 1, 30 - lift, "w" if col == "b" else "s")

    # far legs (darker), behind the body
    leg(8, math.pi, "s")
    leg(19, 0.0, "s")
    # tail
    sway = round(1.5 * math.sin(phase))
    g.line(6, 21 + bob, 3, 17 + bob, "b", width=2)
    g.line(3, 17 + bob, 3 + sway, 12 + bob, "b", width=2)
    g.rect(3 + sway, 11 + bob, 4 + sway, 12 + bob, "s")
    # body
    g.ellipse(14.0, 21.5 + bob, 9.0, 4.4, "b")
    g.ellipse(14.0, 24.0 + bob, 6.0, 1.4, "w")
    # near legs
    leg(10, 0.0, "b")
    leg(21, math.pi, "b")
    # ears
    g.triangle((19, 13 + bob), (20, 6 + bob), (24, 11 + bob), "b")
    g.triangle((24, 11 + bob), (27, 6 + bob), (28, 13 + bob), "b")
    # head
    g.ellipse(23.5, 16.0 + bob, 5.4, 4.8, "b")
    g.triangle((21, 11 + bob), (21, 9 + bob), (22, 11 + bob), "p")
    g.triangle((26, 11 + bob), (26, 9 + bob), (27, 11 + bob), "p")
    # muzzle
    g.ellipse(27.0, 18.0 + bob, 2.2, 1.6, "w")
    g.outline()
    # stripes
    for x in (10, 13, 16):
        g.set(x, 18 + bob, "s")
        g.set(x, 19 + bob, "s")
    g.set(22, 12 + bob, "s")
    g.set(23, 12 + bob, "s")
    # eye
    g.rect(25, 14 + bob, 26, 15 + bob, "e")
    g.set(26, 14 + bob, "h")
    # nose + mouth
    g.set(29, 17 + bob, "p")
    g.set(28, 19 + bob, "o")
    return g


# --------------------------------------------------------------------------
# stretching cat (side view, facing right): a "play bow"
# --------------------------------------------------------------------------

def stretching_cat(t: float, eyes: str) -> Grid:
    """``t`` = 0 standing, 1 full bow (chest down, front legs forward, rear up)."""
    g = Grid()
    hy = 0 if t < 0.5 else -1  # hips rise a little
    cy = 21.5 + 3.5 * t  # chest sinks
    ox, oy = 0, round(4 * t)  # head offset (integer, keeps the small triangles intact)
    hx, hcy = 23.5 + ox, 16.0 + oy
    paw_x = round(20 + 7 * t)  # front paws reach forward
    # far legs (darker)
    g.rect(8, 24, 9, 30, "s")
    g.line(17, cy + 2, paw_x - 2, 29, "s", width=2)
    g.rect(paw_x - 2, 30, paw_x - 1, 30, "s")
    # tail, raised higher in the bow
    tip = round(11 - 4 * t)
    g.line(6, 20 + hy, 3, 16 + hy, "b", width=2)
    g.line(3, 16 + hy, 4, tip, "b", width=2)
    g.rect(4, tip - 1, 5, tip, "s")
    # body: from the hips to the (sinking) chest
    for i in range(9):
        k = i / 8
        g.ellipse(9.0 + 8.0 * k, 20.5 + hy + (cy - 20.5 - hy) * k, 4.4, 4.4, "b")
    g.ellipse(13.5, 23.5 + hy + 2 * t, 4.5, 1.3, "w")
    # near legs
    g.rect(10, 24, 11, 29, "b")
    g.rect(10, 30, 11, 30, "w")
    g.line(19, cy + 2, paw_x, 29, "b", width=2)
    g.rect(paw_x, 30, paw_x + 1, 30, "w")
    # ears and head (same shapes as the walking cat, shifted)

    def p(x, y):
        return (x + ox, y + oy)

    g.triangle(p(19, 13), p(20, 6), p(24, 11), "b")
    g.triangle(p(24, 11), p(27, 6), p(28, 13), "b")
    g.ellipse(hx, hcy, 5.4, 4.8, "b")
    g.triangle(p(21, 11), p(21, 9), p(22, 11), "p")
    g.triangle(p(26, 11), p(26, 9), p(27, 11), "p")
    g.ellipse(hx + 3.5, hcy + 2.0, 2.2, 1.6, "w")
    g.outline()
    # stripes along the back
    for x in (10, 13, 16):
        y = round(17.5 + hy + (cy - 21.5 - hy) * (x - 9) / 8)
        g.set(x, y, "s")
        g.set(x, y + 1, "s")
    ex, ey = p(25, 14)
    if eyes == "open":
        g.rect(ex, ey, ex + 1, ey + 1, "e")
        g.set(ex + 1, ey, "h")
    else:
        g.rect(ex, ey + 1, ex + 1, ey + 1, "o")
    nx, ny = p(29, 17)
    g.set(nx, ny, "p")
    g.set(nx - 1, ny + 2, "o")
    return g


def build_frames() -> dict[str, list[Grid]]:
    frames: dict[str, list[Grid]] = {}
    frames["sit"] = [sitting_cat(i, "open") for i in range(4)]
    frames["blink"] = [sitting_cat(0, e) for e in ("half", "closed", "closed", "half")]
    frames["sleep"] = [sleeping_cat(i) for i in range(4)]
    frames["walk"] = [walking_cat(i, 6) for i in range(6)]
    frames["stretch"] = [stretching_cat(t, e) for t, e in
                         ((0.0, "open"), (0.5, "open"), (1.0, "closed"), (1.0, "closed"),
                          (0.5, "open"), (0.0, "open"))]
    frames["yawn"] = [sitting_cat(0, e, m) for e, m in
                      (("half", "small"), ("closed", "wide"), ("closed", "wide"),
                       ("closed", "wide"), ("closed", "small"), ("half", "closed"))]
    frames["groom"] = [sitting_cat(0, "closed", paw=i) for i in range(4)]
    return frames


def main(out_dir: Path | None = None) -> None:
    from PySide6.QtGui import QColor, QImage

    out_dir = out_dir or Path(__file__).resolve().parent
    frames = build_frames()
    cols = max(n for _, n, _, _ in ANIMATIONS)
    img = QImage(cols * CELL, len(ANIMATIONS) * CELL, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    meta: dict = {"frame_width": CELL, "frame_height": CELL, "animations": {}}
    for row, (name, count, fps, loop) in enumerate(ANIMATIONS):
        assert len(frames[name]) == count, name
        for col, grid in enumerate(frames[name]):
            for y in range(CELL):
                for x in range(CELL):
                    key = grid.px[y][x]
                    if key is not None:
                        img.setPixelColor(col * CELL + x, row * CELL + y, QColor(*PALETTE[key]))
        meta["animations"][name] = {"row": row, "frames": count, "fps": fps, "loop": loop}
    for name in FACES_RIGHT:
        meta["animations"][name]["faces"] = "right"
    if not img.save(str(out_dir / "sprites.png")):
        raise SystemExit("failed to write sprites.png")
    (out_dir / "sprites.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'sprites.png'} and sprites.json")


if __name__ == "__main__":
    main()
