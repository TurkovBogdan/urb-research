"""The sweep: which processes in a table *look* like this checkout's, on evidence alone.

This was the updater's main mechanism and is now its stray detector. `select_kill_targets` is a
pure function over a process table (`Process` records in, `KillTarget`s out with the reason each
matched) and signals nothing at all; `src/core/update/stop.py` decides what happens to a find.

The demotion is the point. The key here is `cwd` plus an argv token — fields readable only for
one's own user on macOS, obtainable on Windows only by reading another process's memory, and
rewritable by the process itself. So a find of this sweep is evidence that something unaccounted
for is running, not permission to signal it: the install's own processes are known from the
registry instead (`src/core/process_registry.py`). Why: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import os
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from src.core.process_table import Process

VETO_ARGV_MARKERS = ("--mcp-", "claude")

# These subcommands act ON the install — the updater's own subprocesses and the stop command —
# so none of them is the served install itself.
NON_SERVICE_SUBCOMMANDS = frozenset({"migrate", "backup", "stop", "update"})

MATCH_LAUNCHER = "launcher"
MATCH_DESCENDANT = "descendant"


@dataclass(frozen=True)
class KillTarget:
    process: Process
    matched_as: str
    parent_pid: int | None = None

    def describe(self) -> str:
        origin = (
            f"{MATCH_DESCENDANT} of {self.parent_pid}"
            if self.matched_as == MATCH_DESCENDANT
            else MATCH_LAUNCHER
        )
        return f"pid {self.process.pid} [{origin}] {self.process.command_line}"


def select_kill_targets(
    processes: Sequence[Process],
    *,
    checkout: Path,
    own_pid: int,
    own_process_group: int,
    own_ancestors: Collection[int] = (),
) -> list[KillTarget]:
    """Launchers of `checkout/src/app.py` (plus `uvicorn src.apps…`) and their descendants.

    The veto applies to descendants too: a shim or an agent session that happens to sit under a
    matched process is still never a find.

    `own_ancestors` is what makes the self-protection hold under `uv run`, which puts the updater
    in a NEW process group: the group rule then covers only the updater's own children, so the
    chain up to the invoking shell is excluded by pid instead.
    """

    def is_protected(process: Process) -> bool:
        return (
            process.pid == own_pid
            or process.pgid == own_process_group
            or process.pid in own_ancestors
            or argv_is_vetoed(process.argv)
        )

    launchers = [
        process
        for process in processes
        if not is_protected(process) and _serves_this_checkout(process, checkout)
    ]

    targets = [KillTarget(process, MATCH_LAUNCHER) for process in launchers]
    selected = {process.pid for process in launchers}
    for launcher in launchers:
        for descendant in descendants(processes, launcher.pid):
            if descendant.pid in selected or is_protected(descendant):
                continue
            selected.add(descendant.pid)
            targets.append(KillTarget(descendant, MATCH_DESCENDANT, parent_pid=launcher.pid))
    return targets


def ancestor_pids(processes: Sequence[Process], pid: int) -> set[int]:
    """The chain of parents above `pid` — the updater's own launcher, shell and terminal."""
    parent_by_pid = {process.pid: process.ppid for process in processes}
    ancestors: set[int] = set()
    parent = parent_by_pid.get(pid)
    while parent is not None and parent not in ancestors:
        ancestors.add(parent)
        parent = parent_by_pid.get(parent)
    return ancestors


def descendants(processes: Sequence[Process], ancestor_pid: int) -> list[Process]:
    """Everything below `ancestor_pid` in the table, nearest generation first."""
    children_by_parent: dict[int, list[Process]] = {}
    for process in processes:
        children_by_parent.setdefault(process.ppid, []).append(process)

    found: list[Process] = []
    visited = {ancestor_pid}
    queue = list(children_by_parent.get(ancestor_pid, ()))
    while queue:
        child = queue.pop(0)
        if child.pid in visited:
            continue
        visited.add(child.pid)
        found.append(child)
        queue.extend(children_by_parent.get(child.pid, ()))
    return found


def argv_is_vetoed(argv: Iterable[str]) -> bool:
    """An MCP shim or an agent session — never a target, wherever it sits in the tree."""
    return any(marker in token for token in argv for marker in VETO_ARGV_MARKERS)


def _serves_this_checkout(process: Process, checkout: Path) -> bool:
    if process.cwd != checkout:
        return False
    entry_index = _entry_token_index(process.argv, checkout)
    if entry_index is None:
        return _runs_uvicorn_app(process.argv)
    return _is_service_launch(process.argv[entry_index + 1:])


def _entry_token_index(argv: Sequence[str], checkout: Path) -> int | None:
    entry_point = checkout / "src" / "app.py"
    for index, token in enumerate(argv):
        if token.endswith("app.py") and _resolve_against(checkout, token) == entry_point:
            return index
    return None


def _resolve_against(checkout: Path, token: str) -> Path:
    candidate = Path(token)
    if not candidate.is_absolute():
        candidate = checkout / candidate
    return Path(os.path.normpath(candidate))


def _is_service_launch(app_arguments: Sequence[str]) -> bool:
    subcommand = next((argument for argument in app_arguments if not argument.startswith("-")), None)
    return subcommand not in NON_SERVICE_SUBCOMMANDS


def _runs_uvicorn_app(argv: Sequence[str]) -> bool:
    runs_uvicorn = any(token == "uvicorn" or token.endswith("/uvicorn") for token in argv)
    return runs_uvicorn and any(token.startswith("src.apps") for token in argv)


__all__ = [
    "MATCH_DESCENDANT",
    "MATCH_LAUNCHER",
    "NON_SERVICE_SUBCOMMANDS",
    "VETO_ARGV_MARKERS",
    "KillTarget",
    "ancestor_pids",
    "argv_is_vetoed",
    "descendants",
    "select_kill_targets",
]
