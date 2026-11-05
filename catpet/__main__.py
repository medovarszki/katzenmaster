"""Entry point: ``python -m catpet`` (or ``python -m catpet --snapshot``)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="catpet", description="A pixel-art cat living on your screen.")
    parser.add_argument("--snapshot", action="store_true",
                        help="render every state headless (offscreen) into PNG files and exit")
    parser.add_argument("--out", type=Path, default=Path("out"), help="output folder for --snapshot")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.snapshot:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"  # must be set before QApplication exists
        from . import snapshot

        return snapshot.run(args.out)

    from . import app

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
