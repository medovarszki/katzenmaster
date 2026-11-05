import logging
import sys
from pathlib import Path

from katzenmaster import __main__ as entry
from katzenmaster import config

ROOT = Path(__file__).resolve().parent.parent


def test_assets_dir_from_source_checkout():
    assert config.assets_dir() == ROOT / "assets" / "sprites"
    assert config.SPRITE_PNG.is_file() and config.SPRITE_JSON.is_file()


def test_assets_dir_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert config.assets_dir() == tmp_path / "assets" / "sprites"


def test_console_streams_left_alone():
    assert entry._ensure_std_streams() is None


def test_windowed_mode_without_std_streams(monkeypatch, tmp_path):
    """A --windowed executable has no stdout/stderr: print must not crash, logs go to a file."""
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(entry.tempfile, "gettempdir", lambda: str(tmp_path))
    log_file = entry._ensure_std_streams()
    assert log_file == tmp_path / "katzenmaster.log"
    print("no crash")
    assert sys.stdout is not None and sys.stderr is not None
    sys.stdout.close()


def test_main_logs_to_file_in_windowed_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(entry.tempfile, "gettempdir", lambda: str(tmp_path))
    ran = []
    import katzenmaster.app

    monkeypatch.setattr(katzenmaster.app, "run", lambda: ran.append(True) or 0)
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers = []
    try:
        assert entry.main([]) == 0
        logging.getLogger("katzenmaster").warning("hello from the test")
        for h in root.handlers:
            h.flush()
        assert "hello from the test" in (tmp_path / "katzenmaster.log").read_text(encoding="utf-8")
    finally:
        for h in root.handlers:
            h.close()
        root.handlers = saved
    assert ran
