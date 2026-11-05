# PyInstaller spec for katzenmaster -- run through packaging/build.py, not directly.
# -*- mode: python -*-
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821 - SPECPATH is injected by PyInstaller
SPRITES = os.path.join(ROOT, "assets", "sprites")
ICON = os.environ.get("KATZENMASTER_ICON")  # written by build.py

# The cat only needs QtCore/QtGui/QtWidgets (+ DBus for the Linux tray). PySide6's hooks
# also collect Qt plugins that drag in QtQuick/QML, QtPdf, QtNetwork and GTK3, which
# roughly doubles the size. Drop them; the platform plugins (windows, xcb, wayland,
# offscreen) stay.
EXCLUDE = re.compile(
    r"""(
        platforminputcontexts[/\\].*virtualkeyboard   # QtQuick-based virtual keyboard
      | imageformats[/\\](lib)?qpdf                  # PDF image format -> QtPdf
      | vectorimageformats[/\\]                      # Lottie -> QtQuick
      | platformthemes[/\\](lib)?qgtk3               # GTK3 theme -> whole GTK stack
      | generic[/\\](lib)?qtuiotouch                 # TUIO touch over the network
      | networkinformation[/\\] | [/\\]tls[/\\]
      | Qt6?(Quick|Qml|Pdf|VirtualKeyboard|Network)[A-Za-z]*\.(so|dll)
      | (^|[/\\])lib(gtk-3|gdk-3|gdk_pixbuf|atk|atk-bridge|atspi|cairo|cairo-gobject|pango|
                     pangocairo|pangoft2|epoxy|cloudproviders|tracker|colord)[-.0-9]*\.so
    )""",
    re.VERBOSE | re.IGNORECASE,
)


def keep(entry):
    return not EXCLUDE.search(entry[0])


a = Analysis(  # noqa: F821
    [os.path.join(ROOT, "packaging", "entry.py")],
    pathex=[ROOT],
    datas=[
        (os.path.join(SPRITES, "sprites.png"), "assets/sprites"),
        (os.path.join(SPRITES, "sprites.json"), "assets/sprites"),
    ],
    excludes=["tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick"],
    noarchive=False,
)
dropped = [e[0] for e in a.binaries + a.datas if not keep(e)]
print(f"katzenmaster.spec: dropping {len(dropped)} unneeded Qt/GTK files", file=sys.stderr)
a.binaries = [e for e in a.binaries if keep(e)]
a.datas = [e for e in a.datas if keep(e)]

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
    upx=False,
    strip=False,
)
