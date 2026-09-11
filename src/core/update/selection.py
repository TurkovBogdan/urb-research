"""Which processes of THIS checkout an update must stop, and stopping them.

`select_kill_targets` is a pure function over a process table (`Process` records in, `KillTarget`s
out with the reason each matched); `plan_kill` runs it against `/proc`; `terminate` signals a plan
and proves the processes are gone. Nothing is signalled unless `terminate(dry_run=False)` is
called explicitly. Why the selection is this strict (cwd + resolved entry point + a veto on
anything MCP- or agent-shaped, then descendants by ppid): `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from src.core.app_path import project_root
from src.core.update.errors import UpdateRefused

VETO_ARGV_MARKERS = ("--mcp-", "claude")

# `migrate`, `backup` and `update` are the updater's own subprocesses, not the served install.
NON_SERVICE_SUBCOMMANDS = frozenset({"migrate", "backup", "update"})

MATCH_LAUNCHER = "launcher"
MATCH_DESCENDANT = "descendant"

TERM_GRACE_SECONDS = 3.0
KILL_GRACE_SECONDS = 3.0
LIVENESS_POLL_SECONDS = 0.2

# A reaped-but-unreported process still shows up in `/proc`; it holds nothing open and writes
# nothing, so for this module it is dead.
ZOMBIE_STATE = "Z"


class ProcessesSurvived(UpdateRefused):
    """Something this checkout runs is still alive after TERM and KILL."""


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
    own_ancestors: Collection[int] = (),
) -> list[KillTarget]:
    """Launchers of `checkout/src/app.py` (plus `uvicorn src.apps…`) and their descendants.

    The veto applies to descendants too: a shim or an agent session that happens to sit under a
    matched process is still never a target.

    `own_ancestors` is what makes the self-protection hold under `uv run`, which puts the updater
    in a NEW process group: the group rule then covers only the updater's own children, so the
    chain up to the invoking shell is excluded by pid instead.
    """

    def is_protected(process: Process) -> bool:
        return (
            process.pid == own_pid
            or process.pgid == own_process_group
            or process.pid in own_ancestors
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
    processes = read_process_table()
    return KillPlan(
        checkout=root,
        targets=select_kill_targets(
            processes,
            checkout=root,
            own_pid=os.getpid(),
            own_process_group=os.getpgrp(),
            own_ancestors=ancestor_pids(processes, os.getpid()),
        ),
    )


def terminate(
    plan: KillPlan, *, dry_run: bool = True, grace_seconds: float = TERM_GRACE_SECONDS
) -> list[int]:
    """TERM the plan, wait out the grace period, KILL the remainder, then prove they are gone.

    Signals are sent ONLY when `dry_run=False` is passed explicitly — the default of this function
    is deliberately harmless, because the cost of a mis-selection here is someone else's install.

    Nothing here trusts a return code: `os.kill` succeeds against a process that ignores TERM, and
    a refused signal is not a dead process either. Liveness is what the caller needs, because a
    survivor writes to the base while `migrate upgrade` rewrites its schema, and SQLite DDL is not
    transactional across revisions.
    """
    if dry_run:
        return []

    for pid in plan.pids:
        _signal(pid, signal.SIGTERM)
    survivors = _wait_for_exit(plan.pids, grace_seconds)
    for pid in survivors:
        _signal(pid, signal.SIGKILL)
    stubborn = _wait_for_exit(survivors, KILL_GRACE_SECONDS)
    if stubborn:
        raise ProcessesSurvived(
            "still alive after TERM and KILL: "
            + ", ".join(str(pid) for pid in stubborn)
            + " — the database stays untouched while anything can still write to it"
        )
    return list(plan.pids)


def process_is_running(pid: int) -> bool:
    """Alive in the only sense that matters here — a zombie holds nothing open."""
    try:
        stat_line = (Path("/proc") / str(pid) / "stat").read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError:
        return False
    try:
        return parse_proc_state(stat_line) != ZOMBIE_STATE
    except IndexError:
        return False


def _wait_for_exit(pids: Sequence[int], timeout: float) -> list[int]:
    """The pids of `pids` still running when the timeout expires."""
    deadline = time.monotonic() + timeout
    alive = [pid for pid in pids if process_is_running(pid)]
    while alive and time.monotonic() < deadline:
        time.sleep(LIVENESS_POLL_SECONDS)
        alive = [pid for pid in alive if process_is_running(pid)]
    return alive


def read_process_table() -> list[Process]:
    processes = (_read_process(pid) for pid in _readable_pids())
    return [process for process in processes if process is not None]


def parse_proc_stat(stat_line: str) -> tuple[int, int]:
    """`(ppid, pgid)` from `/proc/<pid>/stat`."""
    fields = _fields_after_comm(stat_line)
    return int(fields[1]), int(fields[2])


def parse_proc_state(stat_line: str) -> str:
    """The one-letter run state from `/proc/<pid>/stat` (`R`, `S`, `Z`, …)."""
    return _fields_after_comm(stat_line)[0]


def _fields_after_comm(stat_line: str) -> list[str]:
    """Everything past the comm field, which is skipped by its LAST `)`: a process name may
    contain spaces and parentheses, so splitting the whole line shifts every field after it."""
    return stat_line[stat_line.rfind(")") + 1:].split()


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


def ancestor_pids(processes: Sequence[Process], pid: int) -> set[int]:
    """The chain of parents above `pid` — the updater's own launcher, shell and terminal."""
    parent_by_pid = {process.pid: process.ppid for process in processes}
    ancestors: set[int] = set()
    parent = parent_by_pid.get(pid)
    while parent is not None and parent not in ancestors:
        ancestors.add(parent)
        parent = parent_by_pid.get(parent)
    return ancestors


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
    """True when the signal was delivered or the process was already gone.

    A refusal (another user's process) returns False and is otherwise silent on purpose: what the
    caller acts on is whether the process is still running, not whether a signal was accepted.
    """
    try:
        os.kill(pid, sent)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return True


__all__ = [
    "KILL_GRACE_SECONDS",
    "KillPlan",
    "KillTarget",
    "MATCH_DESCENDANT",
    "MATCH_LAUNCHER",
    "NON_SERVICE_SUBCOMMANDS",
    "Process",
    "ProcessesSurvived",
    "TERM_GRACE_SECONDS",
    "VETO_ARGV_MARKERS",
    "ancestor_pids",
    "parse_proc_stat",
    "parse_proc_state",
    "plan_kill",
    "process_is_running",
    "read_process_table",
    "select_kill_targets",
    "terminate",
]
