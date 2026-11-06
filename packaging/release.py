"""Release helpers used by the GitHub Actions workflow (no third-party imports).

    python packaging/release.py check v0.2.0   # tag matches katzenmaster.__version__ and
                                                # CHANGELOG.md has a section for it
    python packaging/release.py notes v0.2.0   # print that CHANGELOG section (release body),
                                                # always UTF-8 encoded
    python packaging/release.py plan           # in CI: decide whether this run releases

``plan`` reads GITHUB_EVENT_NAME, GITHUB_REF, GITHUB_REF_NAME and INPUT_VERSION (the
"Run workflow" form field). A pushed ``v*`` tag, or a manual run on ``main`` with a
version filled in, is a release: the tag is checked like ``check`` does, printed and
written as ``tag=...`` to $GITHUB_OUTPUT. Otherwise the tag is empty (build only).

Exits with status 1 and a message on stderr if a check fails.
"""

from __future__ import annotations

import os
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


RELEASE_BRANCH = "main"


def plan(event: str, ref: str, ref_name: str, input_version: str) -> str:
    """The tag this workflow run releases, or "" for a plain build."""
    if ref.startswith("refs/tags/"):
        tag = ref_name
    elif event == "workflow_dispatch" and input_version.strip():
        if ref != f"refs/heads/{RELEASE_BRANCH}":
            raise ReleaseError(f"releases are made from {RELEASE_BRANCH}, not {ref}; "
                               f"choose '{RELEASE_BRANCH}' in the 'Use workflow from' list")
        version = input_version.strip()
        tag = version if version.startswith("v") else f"v{version}"
    else:
        return ""
    check(tag)
    return tag


def _write_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main(argv: list[str]) -> int:
    valid = (len(argv) == 2 and argv[0] in ("check", "notes")) or argv == ["plan"]
    if not valid:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        if argv[0] == "plan":
            env = os.environ
            tag = plan(env.get("GITHUB_EVENT_NAME", ""), env.get("GITHUB_REF", ""),
                       env.get("GITHUB_REF_NAME", ""), env.get("INPUT_VERSION", ""))
            _write_output("tag", tag)
            print(f"release: {tag}" if tag else "no release: build only")
            return 0
        command, tag = argv
        notes = check(tag)
    except ReleaseError as e:
        print(f"release check failed: {e}", file=sys.stderr)
        return 1
    if command == "notes":
        # always UTF-8, whatever the console encoding is (cp1252 on Windows cannot encode "ő")
        sys.stdout.flush()
        sys.stdout.buffer.write(notes.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        print(f"release check ok: {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
