"""Starting `update.sh` from inside the installation it is about to stop.

The other entry points to the same sequence are a human in a terminal and `app.py update`; this
one is the button on the About page, and it is separate because it cannot wait for the result —
the second step of that sequence kills this process.

Hence the requirements, one line each below: a **detached** session (a child of the backend dies
with it, halfway through a merge), an output sink that outlives the parent (the terminal is long
gone), and two refusals — one for another updater already at work, one for a checkout the
sequence would reject anyway.

It hands over to the script rather than calling `run_update` in-process: the script re-executes
itself through `uv run`, so the update runs on the dependencies it has just synced.
"""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

from src.core import maintenance
from src.core.app_path import AppPath, project_root

UPDATE_SCRIPT_NAME = "update.sh"
SPAWN_LOG_NAME = "update_spawn.log"


class UpdateAlreadyRunning(RuntimeError):
    """An updater is already at work — this process spawned one, or a flag is held."""


class UpdateScriptMissing(RuntimeError):
    """This checkout has no runnable `update.sh` — a partial copy, or the bit is off."""


class CheckoutNotUpdatable(RuntimeError):
    """The sequence would refuse this checkout — say so before stopping anything."""


@dataclass(frozen=True)
class SpawnedUpdate:
    pid: int
    log_path: Path


_spawn_lock = threading.Lock()
_spawned: subprocess.Popen[bytes] | None = None


def script_path() -> Path:
    return project_root() / UPDATE_SCRIPT_NAME


def spawn_update(*, refusal: str | None = None) -> SpawnedUpdate:
    """Start `update.sh` in its own session and return immediately.

    `refusal`, when given, is a precondition the caller already found broken (a dirty tree, a
    checkout on another branch): the update would fail on it several destructive steps later,
    so it is turned down here instead.

    The caller gets only the pid — from here on the update owns the installation, and the next
    thing the browser sees is the backend going away and coming back.
    """
    if refusal:
        raise CheckoutNotUpdatable(refusal)

    script = script_path()
    if not script.is_file():
        raise UpdateScriptMissing(str(script))

    log_path = _log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # The flag goes up several seconds into the run (`uv run`, then `ls-remote`), so it cannot be
    # the only guard: two clicks inside that window would each start an updater. The handle of
    # the one this process started closes the window.
    with _spawn_lock:
        if _spawned is not None and _spawned.poll() is None:
            raise UpdateAlreadyRunning("an update spawned by this process is still running")
        held = maintenance.active()
        if held is not None:
            raise UpdateAlreadyRunning(held.describe())
        return SpawnedUpdate(pid=_start(script, log_path), log_path=log_path)


def _start(script: Path, log_path: Path) -> int:
    global _spawned
    try:
        with open(log_path, "a", encoding="utf-8") as sink:
            _spawned = subprocess.Popen(
                ["bash", str(script)],
                cwd=str(project_root()),
                stdout=sink,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
    except OSError as failure:
        raise UpdateScriptMissing(f"{script}: {failure}") from failure
    return _spawned.pid


def _log_path() -> Path:
    return AppPath.from_root().logs / SPAWN_LOG_NAME


__all__ = [
    "SPAWN_LOG_NAME",
    "UPDATE_SCRIPT_NAME",
    "CheckoutNotUpdatable",
    "SpawnedUpdate",
    "UpdateAlreadyRunning",
    "UpdateScriptMissing",
    "script_path",
    "spawn_update",
]
