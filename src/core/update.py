"""Which processes of THIS checkout an update must stop — selection first, killing second.

Selecting is the dangerous half, so it is a pure function over a process table: give it a list of
`Process` records and it returns the `KillTarget`s it would act on, with the reason each matched.
Nothing is signalled unless `terminate()` is called with `dry_run=False`.

Why a loose pattern is not allowed (`pkill -f app.py` has taken down a session before):

- the coding agent and the MCP stdio shims carry `src/app.py` *inside their own arguments*
  (`--mcp-config`), so argv alone matches them;
- a second install of this project runs the same file name, and its launcher argv may even hold an
  absolute path to its own `src/app.py` — the working directory is what tells the installs apart;
- a `--worker` binds no port, so a listener sweep cannot find it at all;
- hot reload runs a supervisor that holds the socket and respawns its child, and that child's argv
  (`--multiprocessing-fork`) names neither `app.py` nor a role — only the ppid chain finds it.

Hence: entry-point token resolved against this checkout + `cwd` + an explicit veto on anything
MCP- or agent-shaped, then descendants by ppid.
"""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from src.core.app_path import project_root

VETO_ARGV_MARKERS = ("--mcp-", "claude")

# `migrate` and `update` are the updater's own subprocesses, not the served install.
NON_SERVICE_SUBCOMMANDS = frozenset({"migrate", "update"})

MATCH_LAUNCHER = "launcher"
MATCH_DESCENDANT = "descendant"

TERM_GRACE_SECONDS = 3.0


@dataclass(frozen=True)
class Process:
    pid: int
    ppid: int
    pgid: int
    argv: tuple[str, ...] = ()
    cwd: Path | None = None

    @property
    def command_line(self) -> str:
        return " ".join(self.argv)


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


@dataclass(frozen=True)
class KillPlan:
    checkout: Path
    targets: list[KillTarget] = field(default_factory=list)

    @property
    def pids(self) -> list[int]:
        return [target.process.pid for target in self.targets]

    def describe(self) -> str:
        if not self.targets:
            return f"nothing to stop in {self.checkout}"
        lines = [f"would stop {len(self.targets)} process(es) in {self.checkout}:"]
        lines += [f"  {target.describe()}" for target in self.targets]
        return "\n".join(lines)


def select_kill_targets(
    processes: Sequence[Process],
    *,
    checkout: Path,
    own_pid: int,
    own_process_group: int,
) -> list[KillTarget]:
    """Launchers of `checkout/src/app.py` (plus `uvicorn src.apps…`) and their descendants.

    The veto applies to descendants too: a shim or an agent session that happens to sit under a
    matched process is still never a target.
    """

    def is_protected(process: Process) -> bool:
        return (
            process.pid == own_pid
            or process.pgid == own_process_group
            or _argv_is_vetoed(process.argv)
        )

    launchers = [
        process
        for process in processes
        if not is_protected(process) and _serves_this_checkout(process, checkout)
    ]

    targets = [KillTarget(process, MATCH_LAUNCHER) for process in launchers]
    selected = {process.pid for process in launchers}
    for launcher in launchers:
        for descendant in _descendants(processes, launcher.pid):
            if descendant.pid in selected or is_protected(descendant):
                continue
            selected.add(descendant.pid)
            targets.append(KillTarget(descendant, MATCH_DESCENDANT, parent_pid=launcher.pid))
    return targets


def plan_kill(checkout: Path | None = None) -> KillPlan:
    """The same selection against the live `/proc` table. Reads only; signals nothing."""
    root = Path(checkout).resolve() if checkout is not None else project_root()
    return KillPlan(
        checkout=root,
        targets=select_kill_targets(
            read_process_table(),
            checkout=root,
            own_pid=os.getpid(),
            own_process_group=os.getpgrp(),
        ),
    )


def terminate(plan: KillPlan, *, dry_run: bool = True, grace_seconds: float = TERM_GRACE_SECONDS) -> list[int]:
    """TERM the plan, wait out the grace period, KILL whatever is left. Returns signalled pids.

    Signals are sent ONLY when `dry_run=False` is passed explicitly — the default of this function
    is deliberately harmless, because the cost of a mis-selection here is someone else's install.
    """
    if dry_run:
        return []

    signalled = [pid for pid in plan.pids if _signal(pid, signal.SIGTERM)]
    if not signalled:
        return []
    time.sleep(grace_seconds)
    for pid in signalled:
        _signal(pid, signal.SIGKILL)
    return signalled


def read_process_table() -> list[Process]:
    processes = (_read_process(pid) for pid in _readable_pids())
    return [process for process in processes if process is not None]


def parse_proc_stat(stat_line: str) -> tuple[int, int]:
    """`(ppid, pgid)` from `/proc/<pid>/stat`.

    The comm field is skipped by its LAST `)`: a process name may contain spaces and parentheses,
    so splitting the line on whitespace shifts every field after it.
    """
    fields_after_comm = stat_line[stat_line.rfind(")") + 1:].split()
    return int(fields_after_comm[1]), int(fields_after_comm[2])


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


def _argv_is_vetoed(argv: Iterable[str]) -> bool:
    return any(marker in token for token in argv for marker in VETO_ARGV_MARKERS)


def _descendants(processes: Sequence[Process], ancestor_pid: int) -> list[Process]:
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


def _readable_pids() -> list[int]:
    return [int(entry) for entry in os.listdir("/proc") if entry.isdigit()]


def _read_process(pid: int) -> Process | None:
    """A single `/proc` entry, or None when the process vanished mid-read (the table is a race)."""
    proc = Path("/proc") / str(pid)
    try:
        ppid, pgid = parse_proc_stat((proc / "stat").read_text(encoding="utf-8", errors="replace"))
        raw_argv = (proc / "cmdline").read_bytes().decode("utf-8", "replace")
    except (OSError, ValueError, IndexError):
        return None
    return Process(
        pid=pid,
        ppid=ppid,
        pgid=pgid,
        argv=tuple(token for token in raw_argv.split("\0") if token),
        cwd=_read_cwd(proc),
    )


def _read_cwd(proc: Path) -> Path | None:
    try:
        return Path(os.readlink(proc / "cwd")).resolve()
    except OSError:
        return None


def _signal(pid: int, sent: signal.Signals) -> bool:
    try:
        os.kill(pid, sent)
    except OSError:
        return False
    return True


__all__ = [
    "KillPlan",
    "KillTarget",
    "MATCH_DESCENDANT",
    "MATCH_LAUNCHER",
    "NON_SERVICE_SUBCOMMANDS",
    "Process",
    "VETO_ARGV_MARKERS",
    "parse_proc_stat",
    "plan_kill",
    "read_process_table",
    "select_kill_targets",
    "terminate",
]
