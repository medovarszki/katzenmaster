import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QColor, QImage

ROOT = Path(__file__).resolve().parent.parent


def test_snapshot_cli_writes_pngs(tmp_path):
    env = dict(os.environ)
    env.pop("QT_QPA_PLATFORM", None)  # --snapshot must force offscreen by itself
    res = subprocess.run([sys.executable, "-m", "katzenmaster", "--snapshot", "--out", str(tmp_path)],
                         cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stderr
    assert "offscreen" in res.stdout
    names = {p.name for p in tmp_path.iterdir()}
    for state, n in [("sit", 4), ("blink", 4), ("sleep", 4), ("walk_right", 6), ("walk_left", 6),
                     ("stretch_right", 6), ("stretch_left", 6), ("yawn", 6), ("groom", 4)]:
        for i in range(n):
            assert f"{state}_{i}.png" in names
        assert f"strip_{state}.png" in names
    assert "contact_sheet.png" in names

    # raw frames are transparent around the cat, and consecutive frames differ
    for state in ("sit", "sleep", "walk_right", "stretch_right", "yawn", "groom"):
        a = QImage(str(tmp_path / f"{state}_0.png"))
        b = QImage(str(tmp_path / f"{state}_1.png"))
        assert a.hasAlphaChannel()
        assert a.pixelColor(0, 0).alpha() == 0
        assert a != b

    timeline = (tmp_path / "timeline.txt").read_text()
    for word in ("sit", "walk", "blink", "sleep", "chase", "stretch", "yawn", "groom"):
        assert word in timeline


def test_readme_screenshot_script(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("make_screenshot", ROOT / "docs" / "make_screenshot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.render(tmp_path / "shot.png")
    img = QImage(str(out))
    assert (img.width(), img.height()) == (mod.WIDTH * mod.DPR, mod.HEIGHT * mod.DPR)
    # the cat stands on the taskbar: its bottom outline row is right above the bar
    bar_top = (mod.HEIGHT - mod.TASKBAR) * mod.DPR
    cat_cols = range(mod.CAT_X * mod.DPR, (mod.CAT_X + 96) * mod.DPR)
    outline = QColor(43, 29, 22)
    assert any(img.pixelColor(x, bar_top - 1) == outline for x in cat_cols)
    assert (ROOT / "docs" / "screenshot.png").is_file()  # the committed picture exists
