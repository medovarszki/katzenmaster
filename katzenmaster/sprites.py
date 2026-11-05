"""Sprite sheet loading.

The metadata part (``AnimationSpec``, ``load_specs``, ``frame_rect``) is pure Python.
``SpriteSheet`` uses ``QImage`` only (no QApplication / QPixmap needed), so it can be
tested headless as well.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnimationSpec:
    name: str
    row: int
    frames: int
    fps: float
    loop: bool

    @property
    def duration(self) -> float:
        """Length of one pass through the animation, in seconds."""
        return self.frames / self.fps


@dataclass(frozen=True)
class SheetMeta:
    frame_width: int
    frame_height: int
    animations: dict[str, AnimationSpec]


def parse_meta(data: dict) -> SheetMeta:
    anims = {}
    for name, a in data["animations"].items():
        spec = AnimationSpec(
            name=name,
            row=int(a["row"]),
            frames=int(a["frames"]),
            fps=float(a["fps"]),
            loop=bool(a["loop"]),
        )
        if spec.frames <= 0 or spec.fps <= 0:
            raise ValueError(f"animation {name!r}: frames and fps must be positive")
        anims[name] = spec
    return SheetMeta(int(data["frame_width"]), int(data["frame_height"]), anims)


def load_meta(path: Path) -> SheetMeta:
    return parse_meta(json.loads(Path(path).read_text(encoding="utf-8")))


def frame_rect(meta: SheetMeta, anim: str, index: int) -> tuple[int, int, int, int]:
    """(x, y, w, h) of a frame in the sheet."""
    spec = meta.animations[anim]
    if not 0 <= index < spec.frames:
        raise IndexError(f"{anim}: frame {index} out of range 0..{spec.frames - 1}")
    return (index * meta.frame_width, spec.row * meta.frame_height, meta.frame_width, meta.frame_height)


def _mirror(img):
    from PySide6.QtCore import Qt

    if hasattr(img, "flipped"):  # Qt >= 6.9
        return img.flipped(Qt.Orientation.Horizontal)
    return img.mirrored(True, False)


class SpriteSheet:
    """Cuts, scales (nearest neighbour) and mirrors frames; caches the results."""

    def __init__(self, png_path: Path, meta: SheetMeta, scale: int) -> None:
        from PySide6.QtGui import QImage

        if scale < 1 or int(scale) != scale:
            raise ValueError("scale must be a positive integer")
        self.meta = meta
        self.scale = int(scale)
        sheet = QImage(str(png_path))
        if sheet.isNull():
            raise FileNotFoundError(f"cannot load sprite sheet: {png_path}")
        self._sheet = sheet.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        for spec in meta.animations.values():
            x, y, w, h = frame_rect(meta, spec.name, spec.frames - 1)
            if x + w > self._sheet.width() or y + h > self._sheet.height():
                raise ValueError(f"animation {spec.name!r} does not fit into the sheet")
        self._cache: dict[tuple[str, int, bool, int], object] = {}

    @property
    def size(self) -> tuple[int, int]:
        """Size of one scaled frame in pixels."""
        return (self.meta.frame_width * self.scale, self.meta.frame_height * self.scale)

    def frame(self, anim: str, index: int, mirrored: bool = False, scale: int | None = None):
        """Return the scaled (and optionally horizontally mirrored) frame as a QImage.

        ``scale`` defaults to the sheet's scale; it must be a positive integer.
        """
        from PySide6.QtCore import Qt

        scale = self.scale if scale is None else int(scale)
        if scale < 1:
            raise ValueError("scale must be a positive integer")
        key = (anim, index, mirrored, scale)
        img = self._cache.get(key)
        if img is None:
            x, y, w, h = frame_rect(self.meta, anim, index)
            img = self._sheet.copy(x, y, w, h)
            if mirrored:
                img = _mirror(img)
            img = img.scaled(
                w * scale,
                h * scale,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self._cache[key] = img
        return img
