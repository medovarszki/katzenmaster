import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packaging"))
from bundle_filter import keep  # noqa: E402

NEEDED = [
    # Qt modules the app imports (+ DBus for the Linux tray)
    "PySide6/Qt/lib/libQt6Core.so.6", "PySide6/Qt/lib/libQt6Gui.so.6",
    "PySide6/Qt/lib/libQt6Widgets.so.6", "PySide6/Qt/lib/libQt6DBus.so.6",
    "PySide6/Qt/lib/libQt6XcbQpa.so.6", "PySide6/Qt/lib/libQt6WaylandClient.so.6",
    "PySide6/Qt/lib/libQt6OpenGL.so.6", "PySide6/Qt/lib/libicudata.so.73",
    "PySide6\\Qt6Core.dll", "PySide6\\Qt6Gui.dll", "PySide6\\Qt6Widgets.dll",
    # platform plugins: Windows, X11, Wayland, and offscreen for --snapshot
    "PySide6\\plugins\\platforms\\qwindows.dll", "PySide6\\plugins\\platforms\\qoffscreen.dll",
    "PySide6/Qt/plugins/platforms/libqxcb.so", "PySide6/Qt/plugins/platforms/libqwayland.so",
    "PySide6/Qt/plugins/platforms/libqoffscreen.so",
    "PySide6/Qt/plugins/xcbglintegrations/libqxcb-glx-integration.so",
    "PySide6/Qt/plugins/wayland-shell-integration/libxdg-shell.so",
    "PySide6\\plugins\\styles\\qmodernwindowsstyle.dll",
    # our sprites and Python itself
    "assets/sprites/sprites.png", "assets/sprites/sprites.json",
    "python312.dll", "libpython3.12.so.1.0", "libcrypto-3.dll",  # libcrypto only goes with _hashlib
]

DROPPED = [
    "PySide6\\opengl32sw.dll", "PySide6\\d3dcompiler_47.dll",
    "PySide6\\translations\\qtbase_de.qm", "PySide6/Qt/translations/qt_hu.qm",
    "PySide6\\plugins\\imageformats\\qtiff.dll", "PySide6/Qt/plugins/imageformats/libqpdf.so",
    "PySide6\\plugins\\iconengines\\qsvgicon.dll",
    "PySide6\\plugins\\platforms\\qdirect2d.dll", "PySide6\\plugins\\platforms\\qminimal.dll",
    "PySide6/Qt/plugins/platforms/libqeglfs.so", "PySide6/Qt/plugins/platforms/libqvnc.so",
    "PySide6/Qt/plugins/platforms/libqlinuxfb.so", "PySide6/Qt/plugins/platforms/libqminimalegl.so",
    "PySide6/Qt/plugins/platforms/libqvkkhrdisplay.so",
    "PySide6/Qt/plugins/platformthemes/libqgtk3.so",
    "PySide6/Qt/plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so",
    "PySide6/Qt/plugins/wayland-decoration-client/libadwaita.so",
    "PySide6/Qt/lib/libQt6Quick.so.6", "PySide6/Qt/lib/libQt6Qml.so.6",
    "PySide6/Qt/lib/libQt6Pdf.so.6", "PySide6/Qt/lib/libQt6Network.so.6",
    "PySide6/Qt/lib/libQt6Svg.so.6", "PySide6\\Qt6Svg.dll",
    "libgtk-3.so.0", "libcairo.so.2", "libpango-1.0.so.0",
]


@pytest.mark.parametrize("name", NEEDED)
def test_needed_files_are_kept(name):
    assert keep(name)


@pytest.mark.parametrize("name", DROPPED)
def test_unneeded_files_are_dropped(name):
    assert not keep(name)
