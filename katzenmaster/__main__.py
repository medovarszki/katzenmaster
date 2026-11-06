"""Entry point: ``python -m katzenmaster`` (or ``python -m katzenmaster --snapshot``)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

from . import __version__


def _ensure_std_streams() -> Path | None:
    """A windowed (no console) executable has ``sys.stdout``/``sys.stderr`` set to None.

    Then ``print`` would crash and log messages would vanish: send output to devnull and
    return a log file path (``<temp>/katzenmaster.log``) instead.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return None
    devnull = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115 - lives for the process
    sys.stdout = sys.stdout or devnull
    sys.stderr = sys.stderr or devnull
    return Path(tempfile.gettempdir()) / "katzenmaster.log"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="katzenmaster", description="A pixel-art cat living on your screen.")
    parser.add_argument("--snapshot", action="store_true",
                        help="render every state headless (offscreen) into PNG files and exit")
    parser.add_argument("--out", type=Path, default=Path("out"), help="output folder for --snapshot")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    log_file = _ensure_std_streams()  # before parsing: --version / --help print to stdout
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        **({"filename": str(log_file), "filemode": "w", "encoding": "utf-8"}
                           if log_file else {}))

    if args.snapshot:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"  # must be set before QApplication exists
        from . import snapshot

        return snapshot.run(args.out)

    from . import app

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
