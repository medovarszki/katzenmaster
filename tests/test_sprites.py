import pytest
from PySide6.QtGui import QImage

from katzenmaster import config
from katzenmaster.sprites import SpriteSheet, frame_rect, parse_meta

REQUIRED = {"sit", "blink", "sleep", "walk", "stretch", "yawn", "groom"}


def test_meta_has_required_animations(meta):
    assert REQUIRED <= set(meta.animations)
    assert (meta.frame_width, meta.frame_height) == (32, 32)
    rows = [a.row for a in meta.animations.values()]
    assert len(rows) == len(set(rows)), "one animation per row"


def test_loop_flags(meta):
    assert meta.animations["sit"].loop
    assert meta.animations["walk"].loop
    assert meta.animations["sleep"].loop
    assert meta.animations["groom"].loop
    assert not meta.animations["blink"].loop
    assert not meta.animations["stretch"].loop
    assert not meta.animations["yawn"].loop


def test_parse_meta_rejects_bad_values():
    with pytest.raises(ValueError):
        parse_meta({"frame_width": 32, "frame_height": 32,
                    "animations": {"x": {"row": 0, "frames": 0, "fps": 1, "loop": True}}})


def test_frame_rect(meta):
    walk = meta.animations["walk"]
    assert frame_rect(meta, "walk", 2) == (64, walk.row * 32, 32, 32)
    with pytest.raises(IndexError):
        frame_rect(meta, "walk", walk.frames)


def test_default_scale_is_3x(sheet):
    assert config.SCALE == 3
    assert sheet.size == (96, 96)


def _raw_frame(meta, anim, i):
    img = QImage(str(config.SPRITE_PNG)).convertToFormat(QImage.Format.Format_ARGB32)
    return img.copy(*frame_rect(meta, anim, i))


@pytest.mark.parametrize("anim", sorted(REQUIRED))
def test_nearest_neighbour_scaling(meta, sheet, anim):
    s = config.SCALE
    for i in range(meta.animations[anim].frames):
        raw = _raw_frame(meta, anim, i)
        big = sheet.frame(anim, i).convertToFormat(QImage.Format.Format_ARGB32)
        assert (big.width(), big.height()) == (32 * s, 32 * s)
        for y in range(32):
            for x in range(32):
                src = raw.pixel(x, y)
                # every pixel of the s*s block equals the source pixel -> crisp, no blur
                for dy in range(s):
                    for dx in range(s):
                        assert big.pixel(x * s + dx, y * s + dy) == src


@pytest.mark.parametrize("anim", ["walk", "stretch"])
def test_mirroring(meta, sheet, anim):
    for i in range(meta.animations[anim].frames):
        right = sheet.frame(anim, i).convertToFormat(QImage.Format.Format_ARGB32)
        left = sheet.frame(anim, i, mirrored=True).convertToFormat(QImage.Format.Format_ARGB32)
        w = right.width()
        for y in range(0, right.height(), 7):
            for x in range(w):
                assert left.pixel(x, y) == right.pixel(w - 1 - x, y)


def _opaque_bbox(img):
    xs, ys = [], []
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixelColor(x, y).alpha() > 0:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


@pytest.mark.parametrize("anim", sorted(REQUIRED))
def test_frames_are_not_cropped_and_stand_on_ground(meta, anim):
    for i in range(meta.animations[anim].frames):
        raw = _raw_frame(meta, anim, i)
        x0, y0, x1, y1 = _opaque_bbox(raw)
        # nothing touches the left/right/top edges of the cell (would look cut off)
        assert x0 > 0 and y0 > 0 and x1 < 31, (anim, i)
        # feet are on the bottom row so the cat stands on the taskbar edge
        assert y1 == 31, (anim, i)


def test_walk_faces_right(meta):
    """Head (most opaque columns in the upper half) is on the right side of the walk frames."""
    for i in range(meta.animations["walk"].frames):
        raw = _raw_frame(meta, "walk", i)
        left = sum(raw.pixelColor(x, y).alpha() > 0 for y in range(4, 16) for x in range(0, 16))
        right = sum(raw.pixelColor(x, y).alpha() > 0 for y in range(4, 16) for x in range(16, 32))
        assert right > left * 2


@pytest.mark.parametrize("anim", ["walk", "stretch"])
def test_side_view_head_is_on_the_right(meta, anim):
    """All pink pixels (inner ears, nose) are in the right half, also when the head is low."""
    pink = (240, 150, 170)
    for i in range(meta.animations[anim].frames):
        raw = _raw_frame(meta, anim, i)
        xs = [x for y in range(32) for x in range(32)
              if raw.pixelColor(x, y).getRgb()[:3] == pink and raw.pixelColor(x, y).alpha() > 0]
        assert xs and min(xs) >= 16, (anim, i)


def test_sheet_json_marks_side_views():
    import json

    data = json.loads(config.SPRITE_JSON.read_text(encoding="utf-8"))
    faces = {name for name, a in data["animations"].items() if a.get("faces") == "right"}
    assert faces == {"walk", "stretch"}


def test_explicit_scale(sheet):
    assert sheet.frame("sit", 0, scale=1).size().width() == 32
    assert sheet.frame("sit", 0, scale=2).size().width() == 64
    with pytest.raises(ValueError):
        sheet.frame("sit", 0, scale=0)


def test_frame_cache_returns_same_object(sheet):
    assert sheet.frame("sit", 0) is sheet.frame("sit", 0)


def test_missing_png_raises(meta, tmp_path):
    with pytest.raises(FileNotFoundError):
        SpriteSheet(tmp_path / "nope.png", meta, 3)
