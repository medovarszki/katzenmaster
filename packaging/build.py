"""Build a single-file katzenmaster executable for the current OS with PyInstaller.

    pip install -e ".[build]"
    python packaging/build.py

PyInstaller cannot cross-compile: run this on Windows for the .exe and on Linux for
the Linux binary (the GitHub Actions workflow does both). Steps:

1. generate an .ico from the sprite sheet (Windows exe icon),
2. run PyInstaller on ``packaging/katzenmaster.spec`` (one file, no console window, sprites
   bundled, unused Qt plugins/libraries dropped),
3. smoke-test the result: ``<exe> --snapshot`` must render PNGs headless,
4. package: ``dist/katzenmaster-windows-x86_64.exe`` or ``dist/katzenmaster-linux-x86_64.tar.gz``.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from katzenmaster import config  # noqa: E402

DIST = ROOT / "dist"
WORK = ROOT / "build"
NAME = "katzenmaster"


def os_tag() -> str:
    return {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")


def arch_tag() -> str:
    m = platform.machine().lower()
    return {"amd64": "x86_64", "x64": "x86_64", "arm64": "aarch64"}.get(m, m)


def exe_path() -> Path:
    return DIST / (NAME + (".exe" if os_tag() == "windows" else ""))


def make_icon(path: Path) -> Path:
    """Sitting cat, 256 px, nearest neighbour, written as .ico by Qt's image plugin."""
    from katzenmaster.sprites import SpriteSheet, load_meta

    sheet = SpriteSheet(config.SPRITE_PNG, load_meta(config.SPRITE_JSON), 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not sheet.frame("sit", 0, scale=8).save(str(path), "ICO"):
        raise SystemExit(f"could not write icon {path}")
    return path


def run_pyinstaller(icon: Path) -> Path:
    """Build from packaging/katzenmaster.spec (one file, no console, sprites bundled, unused Qt dropped)."""
    import PyInstaller.__main__

    os.environ["KATZENMASTER_ICON"] = str(icon)
    PyInstaller.__main__.run([
        str(ROOT / "packaging" / "katzenmaster.spec"),
        "--noconfirm",
        "--clean",
        "--distpath", str(DIST),
        "--workpath", str(WORK / "pyinstaller"),
    ])
    exe = exe_path()
    if not exe.is_file():
        raise SystemExit(f"PyInstaller did not produce {exe}")
    return exe


def smoke_test(exe: Path) -> None:
    """The bundled app must start and render every state headless."""
    with tempfile.TemporaryDirectory() as tmp:
        res = subprocess.run([str(exe), "--snapshot", "--out", tmp],
                             capture_output=True, text=True, timeout=300)
        pngs = sorted(p.name for p in Path(tmp).glob("*.png"))
        if res.returncode != 0 or "contact_sheet.png" not in pngs or len(pngs) < 20:
            print(res.stdout, res.stderr, sep="\n")
            raise SystemExit(f"smoke test failed: exit={res.returncode}, {len(pngs)} PNGs")
    print(f"smoke test ok: {exe.name} --snapshot rendered {len(pngs)} PNGs")


def package(exe: Path) -> Path:
    stem = f"{NAME}-{os_tag()}-{arch_tag()}"
    if os_tag() == "windows":
        out = DIST / f"{stem}.exe"
        shutil.copy2(exe, out)
    else:
        out = DIST / f"{stem}.tar.gz"  # tar keeps the executable bit (zip artifacts lose it)
        with tarfile.open(out, "w:gz") as tar:
            tar.add(exe, arcname=f"{stem}/{NAME}")
            tar.add(ROOT / "README.md", arcname=f"{stem}/README.md")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-smoke-test", action="store_true")
    args = parser.parse_args()

    icon = make_icon(WORK / "katzenmaster.ico")
    exe = run_pyinstaller(icon)
    if not args.skip_smoke_test:
        smoke_test(exe)
    out = package(exe)
    print(f"built {out.relative_to(ROOT)} ({out.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
