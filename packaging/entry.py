"""PyInstaller entry script (``katzenmaster/__main__.py`` uses relative imports, so it can't be one)."""

import sys

from katzenmaster.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
