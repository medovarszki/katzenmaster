import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packaging"))

import release  # noqa: E402

import katzenmaster  # noqa: E402

CHANGELOG = """# Változások

## [Unreleased]

- még nincs kiadva

## [0.2.0] - 2026-12-01

### Újdonságok
- valami új

## [0.1.0] - 2026-11-06

Az első kiadás.
"""


def test_package_version_is_read_without_importing():
    assert release.package_version() == katzenmaster.__version__
    assert release.package_version('__version__ = "1.2.3"\n') == "1.2.3"
    with pytest.raises(release.ReleaseError):
        release.package_version("nothing here")


def test_pyproject_takes_version_from_the_package():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    assert data["tool"]["setuptools"]["dynamic"]["version"] == {"attr": "katzenmaster.__version__"}


@pytest.mark.parametrize("tag, version", [("v0.1.0", "0.1.0"), ("refs/tags/v1.20.3", "1.20.3"),
                                          ("v1.0.0-rc1", "1.0.0-rc1")])
def test_version_from_tag(tag, version):
    assert release.version_from_tag(tag) == version


@pytest.mark.parametrize("tag", ["0.1.0", "v0.1", "release-1", "v0.1.0 "])
def test_bad_tags_are_rejected(tag):
    with pytest.raises(release.ReleaseError):
        release.version_from_tag(tag)


def test_changelog_section_is_extracted_between_headings():
    assert release.changelog_section("0.2.0", CHANGELOG) == "### Újdonságok\n- valami új\n"
    assert release.changelog_section("0.1.0", CHANGELOG) == "Az első kiadás.\n"
    with pytest.raises(release.ReleaseError):
        release.changelog_section("0.3.0", CHANGELOG)
    with pytest.raises(release.ReleaseError):
        release.changelog_section("1.0.0", "## [1.0.0]\n\n## [0.9.0]\nx\n")  # empty section


def test_current_version_is_releasable():
    """Bumping __version__ without a CHANGELOG section fails here, before tagging."""
    notes = release.check(f"v{katzenmaster.__version__}")
    assert notes.strip()


def test_cli_check_and_notes():
    script = str(ROOT / "packaging" / "release.py")
    tag = f"v{katzenmaster.__version__}"
    # a Windows console encoding that has no "ő": the notes must still come out as UTF-8
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")

    def cli(*args):
        return subprocess.run([sys.executable, script, *args], capture_output=True, env=env)

    ok = cli("check", tag)
    assert ok.returncode == 0, ok.stderr
    notes = cli("notes", tag)
    assert notes.returncode == 0, notes.stderr
    assert notes.stdout.decode("utf-8").replace("\r\n", "\n") == release.check(tag)
    assert "ő".encode("utf-8") in notes.stdout  # the real changelog has Hungarian accents
    bad = cli("check", "v999.0.0")
    assert bad.returncode == 1 and b"does not match" in bad.stderr


def test_version_flag():
    res = subprocess.run([sys.executable, "-m", "katzenmaster", "--version"], cwd=ROOT,
                         capture_output=True, text=True, timeout=60)
    assert res.returncode == 0
    assert res.stdout.strip() == f"katzenmaster {katzenmaster.__version__}"


def test_workflow_releases_what_the_build_produces():
    wf = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in wf
    assert "packaging/release.py check" in wf and "packaging/release.py notes" in wf
    built = set(re.findall(r"file: dist/(\S+)", wf))
    assert built == {"katzenmaster-windows-x86_64.exe", "katzenmaster-linux-x86_64.tar.gz"}
    released = set(re.findall(r"artifacts/(katzenmaster-\S+|SHA256SUMS\.txt)$", wf, re.MULTILINE))
    assert released == built | {"SHA256SUMS.txt"}
