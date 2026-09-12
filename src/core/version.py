"""Release of this checkout — `[project] version` in `pyproject.toml`.

The number lives where a Python project already keeps it, so there is no manifest of our own to
add, to remember or to let drift. `web/package.json` and `uv.lock` copy it; everything served at
runtime (the MCP server banner, the About page) reads it from here, and so does the update: the
version a branch offers is `git show <ref>:pyproject.toml`.

An absent number is `None`, not a number: a checkout older than this scheme, or a branch that
predates it, has no version, and saying `0.0.0` there would be indistinguishable from a real
release. `app_version()` is the one place that substitutes a string, because the MCP banner has
nowhere to put a `None`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from src.core.app_path import project_root

PROJECT_FILE = "pyproject.toml"
# There is no standard field for a release date, so it sits in the project's own tool table.
RELEASE_DATE_TABLE = "urb_research"
UNKNOWN_VERSION = "0.0.0"


@dataclass(frozen=True)
class Release:
    version: str | None
    release_date: str | None


_UNKNOWN = Release(version=None, release_date=None)


def project_file_path() -> Path:
    return project_root() / PROJECT_FILE


def parse_release(text: str) -> Release:
    """The release declared in `pyproject.toml` text; unparsable content has no version.

    Separate from the file read because the same declaration is also obtained without a file —
    `git show <ref>:pyproject.toml` is how an installation learns what its branch offers.
    """
    try:
        document = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return _UNKNOWN

    version = _string_at(document, "project", "version")
    release_date = _string_at(document, "tool", RELEASE_DATE_TABLE, "release_date")
    return Release(version=version, release_date=release_date)


def read_release(path: Path) -> Release:
    """The release declared in the file at `path`; an unreadable file has no version."""
    try:
        return parse_release(path.read_text(encoding="utf-8"))
    except OSError:
        return _UNKNOWN


def installed_release() -> Release:
    """The release of the running checkout.

    Read on every call: it is one small file, and a cache would have to be justified against an
    update that rewrites it under a process that has not restarted yet.
    """
    return read_release(project_file_path())


def app_version() -> str:
    """The number for places that must print something — `0.0.0` when there is none."""
    return installed_release().version or UNKNOWN_VERSION


def _string_at(document: dict[str, object], *path: str) -> str | None:
    """The string at a table path, or `None` if anything along it is missing or another type."""
    node: object = document
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node if isinstance(node, str) and node else None


__all__ = [
    "PROJECT_FILE",
    "RELEASE_DATE_TABLE",
    "Release",
    "UNKNOWN_VERSION",
    "app_version",
    "installed_release",
    "parse_release",
    "project_file_path",
    "read_release",
]
