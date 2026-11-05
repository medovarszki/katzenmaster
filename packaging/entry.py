"""PyInstaller entry script (``catpet/__main__.py`` uses relative imports, so it can't be one)."""

import sys

from catpet.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
