"""Release reader — `[project] version` in `pyproject.toml`, and the copies that must follow it."""

from __future__ import annotations

import json

import pytest

from pathlib import Path

from src.core.app_path import project_root
from src.core.version import (
    PROJECT_FILE,
    UNKNOWN_VERSION,
    app_version,
    installed_release,
    parse_release,
    project_file_path,
    read_release,
)

pytestmark = pytest.mark.pure


def _write(path: Path, text: str) -> Path:
    project_file = path / PROJECT_FILE
    project_file.write_text(text, encoding="utf-8")
    return project_file


def test_reads_version_and_release_date(tmp_path: Path):
    release = read_release(
        _write(
            tmp_path,
            '[project]\nversion = "1.2.3"\n\n[tool.urb_research]\nrelease_date = "2026-09-12"\n',
        )
    )
    assert release.version == "1.2.3"
    assert release.release_date == "2026-09-12"


def test_release_date_is_optional(tmp_path: Path):
    release = read_release(_write(tmp_path, '[project]\nversion = "1.2.3"\n'))
    assert release.version == "1.2.3"
    assert release.release_date is None


def test_missing_file_has_no_version(tmp_path: Path):
    """No declaration means no version — `0.0.0` would be indistinguishable from a release."""
    release = read_release(tmp_path / PROJECT_FILE)
    assert release.version is None
    assert release.release_date is None


def test_torn_file_has_no_version(tmp_path: Path):
    assert read_release(_write(tmp_path, '[project]\nversion = "1.2')).version is None


@pytest.mark.parametrize(
    "text",
    [
        "",
        "[tool.urb_research]\nrelease_date = \"2026-09-12\"\n",
        '[project]\nname = "urb_research"\n',
        "[project]\nversion = 123\n",
        '[project]\nversion = ""\n',
    ],
)
def test_declarations_without_a_usable_version(tmp_path: Path, text: str):
    assert read_release(_write(tmp_path, text)).version is None


def test_non_string_release_date_is_dropped(tmp_path: Path):
    release = read_release(
        _write(tmp_path, '[project]\nversion = "1.2.3"\n\n[tool.urb_research]\nrelease_date = 20260912\n')
    )
    assert release.version == "1.2.3"
    assert release.release_date is None


def test_app_version_substitutes_a_string_where_none_is_impossible(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """The MCP banner has nowhere to put a `None`; everything else keeps the honest absence."""
    monkeypatch.setattr("src.core.version.project_file_path", lambda: tmp_path / PROJECT_FILE)
    assert app_version() == UNKNOWN_VERSION


def test_this_project_declares_a_release():
    """The number the installation reports comes from the repository's own `pyproject.toml`."""
    assert project_file_path().name == PROJECT_FILE
    assert installed_release().version is not None
    assert app_version() == installed_release().version


def test_the_copies_of_the_number_have_not_drifted():
    """`pyproject.toml` declares; the web package and the lock only copy.

    Drift is the one risk the release checklist names out loud, and it is silent by nature — a
    forgotten copy shows up as two different numbers in two different places months later.
    """
    version = installed_release().version
    root = project_root()

    web_package = json.loads((root / "web" / "package.json").read_text(encoding="utf-8"))
    lock_entry = f'name = "urb-research"\nversion = "{version}"'

    assert web_package["version"] == version
    assert lock_entry in (root / "uv.lock").read_text(encoding="utf-8")
