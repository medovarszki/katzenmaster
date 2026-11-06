# PyInstaller spec for katzenmaster -- run through packaging/build.py, not directly.
# -*- mode: python -*-
import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821 - SPECPATH is injected by PyInstaller
SPRITES = os.path.join(ROOT, "assets", "sprites")
ICON = os.environ.get("KATZENMASTER_ICON")  # written by build.py

sys.path.insert(0, SPECPATH)  # noqa: F821
from bundle_filter import keep  # noqa: E402 - see bundle_filter.py for what is dropped and why


a = Analysis(  # noqa: F821
    [os.path.join(ROOT, "packaging", "entry.py")],
    pathex=[ROOT],
    datas=[
        (os.path.join(SPRITES, "sprites.png"), "assets/sprites"),
        (os.path.join(SPRITES, "sprites.json"), "assets/sprites"),
    ],
    excludes=[
        "tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick",
        # OpenSSL bindings (-> libcrypto/libssl). Nothing needs TLS; hashlib falls back
        # to its built-in implementations without _hashlib.
        "ssl", "_ssl", "_hashlib",
    ],
    noarchive=False,
)
dropped = [e[0] for e in a.binaries + a.datas if not keep(e[0])]
print(f"katzenmaster.spec: dropping {len(dropped)} unneeded Qt/GTK files", file=sys.stderr)
a.binaries = [e for e in a.binaries if keep(e[0])]
a.datas = [e for e in a.datas if keep(e[0])]

pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="katzenmaster",
    console=False,  # no console window on Windows
    icon=ICON if ICON and sys.platform == "win32" else None,
    upx=False,  # UPX triggers antivirus false positives and can break Qt plugins
    strip=sys.platform.startswith("linux"),  # drop debug symbols (libpython, Qt libs)
)
