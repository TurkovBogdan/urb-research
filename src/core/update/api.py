"""HTTP surface of the update (mounted at /internal/core/update).

Three routes for three costs. `GET ""` is local and instant — it is what the About page opens
with. `POST "/check"` fetches, so it is slow, may fail, and is a POST because it changes the
checkout's tracking refs. `POST "/start"` hands the installation over to `update.sh` and answers
before this process goes down.

The handlers are **sync** on purpose: each one shells out to git, and a blocking call in an
`async def` would freeze the event loop — health, MCP and every other page with it. FastAPI runs
a `def` handler in a threadpool.

No `@guard` here: the zone default applies, so the day an auth module arrives these routes are
covered by it. A route that can stop the installation must not be the one that opted out.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.core.api import ApiError
from src.core.update import spawn, status

router = APIRouter()

UPSTREAM_UNREACHABLE = 502
SPAWN_FAILED = 500

REFUSAL_DIRTY_TREE = "dirty_tree"
REFUSAL_BRANCH_MISMATCH = "branch_mismatch"


def _followed_branch(request: Request) -> str:
    return request.app.state.config.update_branch


def _refusal(installation: status.Installation) -> str | None:
    """Why the sequence would turn this checkout down — a code, not a sentence.

    The page is Russian and the backend has no locale; prose here would arrive on screen in
    English. Same contract as the rest of the API: the server names the reason, the frontend
    says it.
    """
    if installation.dirty:
        return REFUSAL_DIRTY_TREE
    if not installation.branch_matches:
        return REFUSAL_BRANCH_MISMATCH
    return None


@router.get("")
def get_installation(request: Request) -> dict[str, Any]:
    """What is installed here: the release, the build under it, and whether it may be updated."""
    installation = status.installation(followed_branch=_followed_branch(request))
    return {
        "version": installation.version,
        "release_date": installation.release_date,
        "followed_branch": installation.followed_branch,
        "checked_out_branch": installation.checked_out_branch,
        "branch_matches": installation.branch_matches,
        "commit": installation.commit,
        "describes_as": installation.describes_as,
        "dirty": installation.dirty,
        "refusal": _refusal(installation),
    }


@router.post("/check")
def check_upstream(request: Request) -> dict[str, Any]:
    """Ask the remote what the followed branch offers. Fetches — expect it to take a moment."""
    try:
        upstream = status.upstream(followed_branch=_followed_branch(request))
    except status.UpstreamBranchMissing as missing:
        raise ApiError.conflict(str(missing), code="upstream_branch_missing") from missing
    except status.UpstreamUnreachable as unreachable:
        raise ApiError(
            UPSTREAM_UNREACHABLE, str(unreachable), code="upstream_unreachable"
        ) from unreachable
    return {
        "branch": upstream.branch,
        "version": upstream.version,
        "commit": upstream.commit,
        "behind": upstream.behind,
        "ahead": upstream.ahead,
    }


@router.post("/start")
def start_update(request: Request) -> dict[str, Any]:
    """Start the update and answer while it is still raising its flag.

    Nothing is awaited here on purpose: the very next steps of that process stop this one.
    """
    installation = status.installation(followed_branch=_followed_branch(request))
    refusal = _refusal(installation)
    try:
        started = spawn.spawn_update(refusal=refusal)
    except spawn.UpdateAlreadyRunning as held:
        raise ApiError.conflict(str(held), code="update_already_running") from held
    except spawn.CheckoutNotUpdatable as unusable:
        raise ApiError.conflict(str(unusable), code=refusal) from unusable
    except spawn.UpdateScriptMissing as broken:
        raise ApiError(SPAWN_FAILED, str(broken), code="update_script_missing") from broken
    return {"status": "started", "pid": started.pid, "log": str(started.log_path)}


__all__ = ["router"]
