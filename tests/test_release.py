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


def _workflow():
    return (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")


def test_workflow_releases_what_the_build_produces():
    wf = _workflow()
    assert 'tags: ["v*"]' in wf
    assert "packaging/release.py plan" in wf and "packaging/release.py notes" in wf
    built = set(re.findall(r"file: dist/(\S+)", wf))
    assert built == {"katzenmaster-windows-x86_64.exe", "katzenmaster-linux-x86_64.tar.gz"}
    released = set(re.findall(r"artifacts/(katzenmaster-\S+|SHA256SUMS\.txt)$", wf, re.MULTILINE))
    assert released == built | {"SHA256SUMS.txt"}


def test_workflow_has_a_run_workflow_release_form():
    wf = _workflow()
    assert re.search(r"workflow_dispatch:\n\s+inputs:\n\s+version:", wf)
    # the free-text field only reaches scripts through env (no script injection)
    run_lines = [ln for ln in wf.splitlines() if "run:" in ln or ln.startswith(" " * 10)]
    assert not any("inputs.version" in ln for ln in run_lines if "INPUT_VERSION:" not in ln)
    assert "INPUT_VERSION: ${{ inputs.version }}" in wf
    # build waits for the checks; release only when plan says so
    assert "needs: plan" in wf and "needs: [plan, build]" in wf
    assert "if: needs.plan.outputs.tag != ''" in wf


# ------------------------------------------------------------------ plan
V = katzenmaster.__version__


def test_plain_pushes_and_manual_builds_do_not_release():
    assert release.plan("push", "refs/heads/main", "main", "") == ""
    assert release.plan("workflow_dispatch", "refs/heads/main", "main", "") == ""
    assert release.plan("workflow_dispatch", "refs/heads/main", "main", "   ") == ""
    assert release.plan("pull_request", "refs/pull/1/merge", "1/merge", "") == ""


def test_pushed_tag_releases():
    assert release.plan("push", f"refs/tags/v{V}", f"v{V}", "") == f"v{V}"
    with pytest.raises(release.ReleaseError, match="does not match"):
        release.plan("push", "refs/tags/v999.0.0", "v999.0.0", "")


@pytest.mark.parametrize("typed", [V, f"v{V}", f" {V} "])
def test_manual_release_from_main(typed):
    assert release.plan("workflow_dispatch", "refs/heads/main", "main", typed) == f"v{V}"


def test_manual_release_checks_version_and_branch():
    with pytest.raises(release.ReleaseError, match="does not match"):
        release.plan("workflow_dispatch", "refs/heads/main", "main", "999.0.0")
    with pytest.raises(release.ReleaseError, match="not like"):
        release.plan("workflow_dispatch", "refs/heads/main", "main", "latest")
    with pytest.raises(release.ReleaseError, match="from main"):
        release.plan("workflow_dispatch", "refs/heads/feature", "feature", V)


def test_cli_plan_writes_github_output(tmp_path):
    script = str(ROOT / "packaging" / "release.py")
    out = tmp_path / "out.txt"
    base = dict(os.environ, GITHUB_OUTPUT=str(out), GITHUB_EVENT_NAME="workflow_dispatch",
                GITHUB_REF="refs/heads/main", GITHUB_REF_NAME="main")

    def plan(**env):
        out.write_text("")
        res = subprocess.run([sys.executable, script, "plan"], capture_output=True, text=True,
                             env=dict(base, **env))
        return res, out.read_text()

    res, written = plan(INPUT_VERSION=V)
    assert res.returncode == 0 and written == f"tag=v{V}\n"
    res, written = plan(INPUT_VERSION="")
    assert res.returncode == 0 and written == "tag=\n"
    res, written = plan(INPUT_VERSION="999.0.0")
    assert res.returncode == 1 and "does not match" in res.stderr and written == ""
