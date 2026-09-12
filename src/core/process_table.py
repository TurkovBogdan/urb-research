"""The live process table: who is running, under whom, from where, and since when.

Read through `psutil` rather than `/proc`, because the updater has to stop the processes of its
own installation on whatever the operator runs — and procfs is Linux-only, so a macOS install
crashed on `os.listdir("/proc")` before it stopped anything (2026-09-12).

A process this user may not read is left out of the table entirely: it is also a process this
program could not have signalled. Liveness, on the other hand, does NOT hide that case: a process
of another user is alive and writing, and treating it as dead is how a migration ends up running
beside a live writer. Who is selected out of the table, and why: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import enum
import os
from dataclasses import dataclass
from pathlib import Path

import psutil

# Two readers of the same pid must agree on its start time, or every identity check fails. psutil
# derives it from the boot time plus the kernel's start ticks, so the readings differ only in the
# last decimals of the conversion.
START_TIME_TOLERANCE_SECONDS = 0.01


class Liveness(enum.Enum):
    """What a pid is, for the only purpose this module serves — may it still write to the base.

    `GONE` covers a zombie and a reused pid: neither holds anything open. `FOREIGN` is a live
    process this user cannot read or signal — the answer that must never be rounded down to
    `GONE`, because the update would then migrate beside it.
    """

    ALIVE = "alive"
    GONE = "gone"
    FOREIGN = "foreign"


@dataclass(frozen=True)
class Process:
    pid: int
    ppid: int
    pgid: int | None = None
    start_time: float = 0.0
    argv: tuple[str, ...] = ()
    cwd: Path | None = None

    @property
    def command_line(self) -> str:
        return " ".join(self.argv)


def read_process_table() -> list[Process]:
    """Every process readable at this moment; the table is a race and never claims otherwise."""
    records = (_read_process(pid) for pid in psutil.pids())
    return [record for record in records if record is not None]


def process_liveness(pid: int, *, start_time: float | None = None) -> Liveness:
    """Whether the pid can still write — with `start_time`, whether it is still the SAME process.

    Without the start time this cannot tell a survivor from a stranger that inherited the number,
    which is the whole reason every caller here carries one.
    """
    try:
        process = psutil.Process(pid)
        if start_time is not None and not _started_at(process, start_time):
            return Liveness.GONE
        return Liveness.GONE if process.status() == psutil.STATUS_ZOMBIE else Liveness.ALIVE
    except psutil.NoSuchProcess:
        return Liveness.GONE
    except (psutil.AccessDenied, PermissionError):
        return Liveness.FOREIGN
    except (psutil.Error, OSError):
        return Liveness.GONE


def process_is_running(pid: int, *, start_time: float | None = None) -> bool:
    """Alive in the only sense that matters here — a foreign process counts as running."""
    return process_liveness(pid, start_time=start_time) is not Liveness.GONE


def process_start_time(pid: int) -> float | None:
    """When the process began, or None when it is gone or unreadable — the identity half of a pid."""
    try:
        return psutil.Process(pid).create_time()
    except (psutil.Error, OSError):
        return None


def process_argv(pid: int) -> str | None:
    """The command line as one string, or None when the process is gone or unreadable."""
    try:
        return " ".join(psutil.Process(pid).cmdline())
    except (psutil.Error, OSError):
        return None


def _read_process(pid: int) -> Process | None:
    """One row, or None when the process vanished mid-read or belongs to another user."""
    try:
        process = psutil.Process(pid)
        ppid = process.ppid()
        argv = _read_argv(process)
        start_time = process.create_time()
    except (psutil.Error, OSError):
        return None
    return Process(
        pid=pid,
        ppid=ppid,
        pgid=_read_process_group(pid),
        start_time=start_time,
        argv=argv,
        cwd=_read_cwd(process),
    )


def _read_argv(process: psutil.Process) -> tuple[str, ...]:
    """Blank arguments are dropped: a process that rewrote its own argv (browsers do) leaves the
    space it no longer uses as empty slots, and they are part of no command line."""
    return tuple(token for token in process.cmdline() if token)


def _read_process_group(pid: int) -> int | None:
    """None where the platform has no process groups at all — Windows, where `os.getpgid` is
    absent and an `AttributeError` would crash the updater before it stopped anything."""
    if not hasattr(os, "getpgid"):
        return None
    try:
        return os.getpgid(pid)
    except OSError:
        return None


def _read_cwd(process: psutil.Process) -> Path | None:
    """None is a normal answer: macOS refuses another user's working directory, and Linux
    refuses a kernel thread's."""
    try:
        return Path(process.cwd()).resolve()
    except (psutil.Error, OSError):
        return None


def _started_at(process: psutil.Process, start_time: float) -> bool:
    return abs(process.create_time() - start_time) <= START_TIME_TOLERANCE_SECONDS


__all__ = [
    "START_TIME_TOLERANCE_SECONDS",
    "Liveness",
    "Process",
    "process_argv",
    "process_is_running",
    "process_liveness",
    "process_start_time",
    "read_process_table",
]
