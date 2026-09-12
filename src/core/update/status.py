"""Is this installation behind, and may it be updated at all — read-only.

Two readings, deliberately apart. `installation` is local and cheap: the manifest plus the
commit under it. `upstream` talks to the remote — it fetches, so it is slow, can fail, and is
never done to answer a page load by itself.

The same facts the command checks before it does anything (`sequence._verify_preconditions`):
the branch, a clean tree, the distance to the remote head. Read here, enforced there — which is
why this lives next to the command and reuses its git conventions instead of inventing its own.

Everything unknown is `None`. A checkout without git, a failed `rev-list`, a branch that predates
the manifest — each of those is «I could not tell», and a zero in its place would be a claim.
"""

from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from src.core.app_path import project_root
from src.core.update.sequence import (
    FETCH_TIMEOUT_SECONDS,
    GIT_NONINTERACTIVE,
    INSPECT_TIMEOUT_SECONDS,
    REMOTE,
    validate_branch,
)
from src.core.version import PROJECT_FILE, Release, installed_release, parse_release

# One fetch at a time per process: two open tabs would otherwise race for the same `.git` locks
# and report failures that are nothing but each other.
_fetch_lock = threading.Lock()


class UpstreamUnreachable(RuntimeError):
    """The remote could not be asked — no network, no credentials, a timeout."""


class UpstreamBranchMissing(RuntimeError):
    """The remote answered and has no such branch — a configuration mistake, not an outage."""


@dataclass(frozen=True)
class Installation:
    """What is installed here: the release, the checkout under it, and its drift."""

    version: str | None
    release_date: str | None
    followed_branch: str
    checked_out_branch: str | None
    commit: str | None
    describes_as: str | None
    dirty: bool | None

    @property
    def branch_matches(self) -> bool:
        """The command fast-forwards `followed_branch` and refuses when the checkout is elsewhere."""
        return self.checked_out_branch == self.followed_branch


@dataclass(frozen=True)
class UpstreamHead:
    """The head of the followed branch, and how this installation stands against it."""

    branch: str
    version: str | None
    commit: str
    behind: int | None
    ahead: int | None


def installation(*, followed_branch: str) -> Installation:
    """Local facts only — no network, no writes."""
    local = installed_release()
    return Installation(
        version=local.version,
        release_date=local.release_date,
        followed_branch=followed_branch,
        checked_out_branch=_git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        commit=_git_text(["rev-parse", "--short", "HEAD"]),
        describes_as=_git_text(["describe", "--tags", "--long", "--dirty"]),
        dirty=_dirty(),
    )


def upstream(*, followed_branch: str) -> UpstreamHead:
    """Fetch, then read the branch head: its manifest and the distance in both directions.

    The fetch updates tracking refs only — the checkout is not touched, so this stays safe to
    call while the installation serves.
    """
    validate_branch(followed_branch)
    _fetch()

    ref = f"{REMOTE}/{followed_branch}"
    commit = _git_text(["rev-parse", "--short", ref])
    if commit is None:
        raise UpstreamBranchMissing(f"{REMOTE} has no branch {followed_branch!r}")

    behind, ahead = _distance(ref)
    return UpstreamHead(
        branch=followed_branch,
        version=_release_at(ref).version,
        commit=commit,
        behind=behind,
        ahead=ahead,
    )


def _dirty() -> bool | None:
    """`None` when git could not be asked — «clean» must not be claimed out of ignorance."""
    listed = _git_text(["status", "--porcelain"])
    return None if listed is None else bool(listed)


def _fetch() -> None:
    with _fetch_lock:
        result = _git(["fetch", REMOTE], timeout=FETCH_TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise UpstreamUnreachable(result.stderr.strip() or f"could not reach {REMOTE}")


def _release_at(ref: str) -> Release:
    """The release declared on `ref` — a branch that predates the scheme has no version."""
    return parse_release(_git_text(["show", f"{ref}:{PROJECT_FILE}"]) or "")


def _distance(ref: str) -> tuple[int | None, int | None]:
    """Commits behind and ahead of `ref`; `(None, None)` when git would not answer.

    Ahead matters as much as behind: the update fast-forwards, so a local commit the remote has
    never seen turns it into a refusal.
    """
    counted = _git_text(["rev-list", "--left-right", "--count", f"HEAD...{ref}"])
    if counted is None:
        return None, None

    parts = counted.split()
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None, None
    ahead, behind = (int(part) for part in parts)
    return behind, ahead


def _git_text(argv: Sequence[str]) -> str | None:
    """Stdout of a successful git command, stripped; `None` when it failed or git is missing."""
    result = _git(argv)
    return result.stdout.strip() if result.returncode == 0 else None


def _git(
    argv: Sequence[str], *, timeout: float = INSPECT_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[str]:
    """Never raises: a checkout without git, or a git that hangs, is a fact to report, not a
    failure to propagate — every caller above turns a non-zero return into «unknown»."""
    try:
        return subprocess.run(
            ["git", *argv],
            cwd=_checkout(),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **GIT_NONINTERACTIVE},
        )
    except subprocess.TimeoutExpired as expired:
        return subprocess.CompletedProcess(
            args=list(argv), returncode=-1, stdout="", stderr=f"git timed out: {expired}"
        )
    except (OSError, subprocess.SubprocessError) as failure:
        return subprocess.CompletedProcess(
            args=list(argv), returncode=-1, stdout="", stderr=f"git could not be run: {failure}"
        )


def _checkout() -> Path:
    return project_root()


__all__ = [
    "Installation",
    "UpstreamBranchMissing",
    "UpstreamHead",
    "UpstreamUnreachable",
    "installation",
    "upstream",
]
