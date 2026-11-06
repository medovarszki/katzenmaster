"""Which collected files to leave out of the bundle (used by katzenmaster.spec, tested)."""

import re

# The cat only needs QtCore/QtGui/QtWidgets (+ DBus for the Linux tray) and paints with
# the raster engine. PySide6's hooks collect much more; everything below is dropped.
EXCLUDE = re.compile(
    r"""(
        platforminputcontexts[/\\].*virtualkeyboard  # QtQuick-based virtual keyboard
      | imageformats[/\\]                          # sprites are PNG, built into QtGui
      | iconengines[/\\]                           # SVG icon engine
      | vectorimageformats[/\\]                    # Lottie -> QtQuick
      | platformthemes[/\\](lib)?qgtk3             # GTK3 theme -> whole GTK stack
      | generic[/\\](lib)?qtuiotouch               # TUIO touch over the network
      | egldeviceintegrations[/\\]                 # only for the eglfs platform
      | wayland-decoration-client[/\\](lib)?adwaita  # needs QtSvg; the window is frameless
      | networkinformation[/\\] | [/\\]tls[/\\]
      | (^|[/\\])translations[/\\]               # Qt's own dialog texts; we have none
      # platform plugins: keep only windows, xcb, wayland and offscreen (--snapshot)
      | platforms[/\\](?!(lib)?q(windows|xcb|wayland|offscreen)\.)
      | opengl32sw\.dll | d3dcompiler_\d+\.dll     # software OpenGL / D3D shader compiler
      | Qt6?(Quick|Qml|Pdf|VirtualKeyboard|Network|Svg)[A-Za-z]*\.(so|dll)
      | (^|[/\\])lib(gtk-3|gdk-3|gdk_pixbuf|atk|atk-bridge|atspi|cairo|cairo-gobject|pango|
                     pangocairo|pangoft2|epoxy|cloudproviders|tracker|colord)[-.0-9]*\.so
    )""",
    re.VERBOSE | re.IGNORECASE,
)


def keep(dest_name: str) -> bool:
    """True if a bundled file (destination path inside the bundle) is needed."""
    return not EXCLUDE.search(dest_name)
