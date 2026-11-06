"""Release helpers used by the GitHub Actions workflow (no third-party imports).

    python packaging/release.py check v0.2.0   # tag matches katzenmaster.__version__ and
                                                # CHANGELOG.md has a section for it
    python packaging/release.py notes v0.2.0   # print that CHANGELOG section (release body)

Exits with status 1 and a message on stderr if the check fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "katzenmaster" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
_HEADING_RE = re.compile(r"^## \[?v?(?P<version>[0-9][^\]\s]*)\]?.*$", re.MULTILINE)


class ReleaseError(Exception):
    pass


def package_version(init_text: str | None = None) -> str:
    text = INIT.read_text(encoding="utf-8") if init_text is None else init_text
    m = _VERSION_RE.search(text)
    if not m:
        raise ReleaseError(f"no __version__ in {INIT}")
    return m.group(1)


def version_from_tag(tag: str) -> str:
    tag = tag.removeprefix("refs/tags/")
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[-.]?[0-9A-Za-z.]+)?", tag):
        raise ReleaseError(f"tag {tag!r} is not like v1.2.3")
    return tag[1:]


def changelog_section(version: str, changelog_text: str | None = None) -> str:
    """Body of the ``## [version]`` section of CHANGELOG.md, without the heading."""
    text = CHANGELOG.read_text(encoding="utf-8") if changelog_text is None else changelog_text
    headings = list(_HEADING_RE.finditer(text))
    for i, h in enumerate(headings):
        if h.group("version") == version:
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            body = text[h.end():end].strip()
            if not body:
                raise ReleaseError(f"CHANGELOG.md section for {version} is empty")
            return body + "\n"
    raise ReleaseError(f"CHANGELOG.md has no '## [{version}]' section")


def check(tag: str) -> str:
    version = version_from_tag(tag)
    current = package_version()
    if version != current:
        raise ReleaseError(f"tag {tag} does not match katzenmaster.__version__ = {current!r}; "
                           "bump the version (katzenmaster/__init__.py) before tagging")
    return changelog_section(version)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("check", "notes"):
        print(__doc__, file=sys.stderr)
        return 2
    command, tag = argv
    try:
        notes = check(tag)
    except ReleaseError as e:
        print(f"release check failed: {e}", file=sys.stderr)
        return 1
    if command == "notes":
        sys.stdout.write(notes)
    else:
        print(f"release check ok: {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
