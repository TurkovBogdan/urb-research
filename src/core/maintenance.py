"""Maintenance flag — «an update is in progress, do not launch anything».

Two files at the **project root**, not under `runtime/<APP_ENV>/`: `runtime/maintenance.lock`, an
advisory lock the kernel releases however the updater dies, and `runtime/maintenance.json`, the
readable half — who holds it, since when and why. The lock is the mutual exclusion between two
updaters; the JSON is what every other process reads, and it is active only while its pid is
still the process that wrote it. `begin` raises `MaintenanceHeld` when someone got there first,
`end` releases both. Imports stay at the process table and the stdlib: the flag is read before
`Config()` and before any database import. Why the path and the liveness rule are what they are:
`AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from src.core.app_path import project_root
from src.core.process_table import process_argv, process_is_running, process_start_time

try:
    import fcntl
except ModuleNotFoundError:  # pragma: no cover — Windows, where the update refuses earlier
    fcntl = None  # type: ignore[assignment]

MAX_AGE_SECONDS = 3600

# An updater is `src/app.py update`; both markers must be present, so a plain backend that
# happens to reuse the pid is not mistaken for one.
UPDATER_ARGV_MARKERS = ("app.py", "update")

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

_held_lock: IO[str] | None = None


class MaintenanceHeld(RuntimeError):
    """Another updater holds the flag."""


@dataclass(frozen=True)
class MaintenanceFlag:
    pid: int
    started_at: datetime
    reason: str
    start_time: float | None = None

    def as_json(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "started_at": self.started_at.strftime(_TIMESTAMP_FORMAT),
            "reason": self.reason,
            "start_time": self.start_time,
        }

    @staticmethod
    def from_json(payload: dict[str, object]) -> "MaintenanceFlag":
        recorded_start = payload.get("start_time")
        return MaintenanceFlag(
            pid=int(payload["pid"]),  # type: ignore[arg-type]
            started_at=datetime.strptime(str(payload["started_at"]), _TIMESTAMP_FORMAT),
            reason=str(payload.get("reason", "")),
            start_time=None if recorded_start is None else float(recorded_start),  # type: ignore[arg-type]
        )

    def age_seconds(self, now: datetime | None = None) -> float:
        return ((now or _utc_now()) - self.started_at).total_seconds()

    def is_live(self, now: datetime | None = None) -> bool:
        within_age_bound = self.age_seconds(now) < MAX_AGE_SECONDS
        return within_age_bound and self._process_still_holds_it()

    def describe(self) -> str:
        started = self.started_at.strftime(_TIMESTAMP_FORMAT)
        return f"pid {self.pid}, since {started}: {self.reason}"

    def _process_still_holds_it(self) -> bool:
        """Identity by pid + start time; a flag from before the start time was recorded falls back
        to the argv check, so an update in progress is still honoured across this very change."""
        if self.start_time is None:
            return process_is_updater(self.pid)
        return process_is_running(self.pid, start_time=self.start_time)


def flag_path() -> Path:
    return project_root() / "runtime" / "maintenance.json"


def lock_path() -> Path:
    return project_root() / "runtime" / "maintenance.lock"


def process_is_updater(pid: int) -> bool:
    """The pid is alive AND its argv still looks like `src/app.py update` (pid-reuse guard)."""
    if not process_is_running(pid):
        return False
    argv = process_argv(pid)
    return argv is not None and all(marker in argv for marker in UPDATER_ARGV_MARKERS)


def read() -> MaintenanceFlag | None:
    """The flag as written, or None when it is absent or unreadable (a torn write counts as gone)."""
    try:
        payload = json.loads(flag_path().read_text(encoding="utf-8"))
        return MaintenanceFlag.from_json(payload)
    except (OSError, ValueError, KeyError, TypeError):
        return None


def active() -> MaintenanceFlag | None:
    """The flag while a live updater holds it, else None — `is_active()` keeping the details,
    so a refusing caller can name who holds it and why."""
    flag = read()
    return flag if flag is not None and flag.is_live() else None


def is_active() -> bool:
    return active() is not None


def begin(reason: str) -> MaintenanceFlag:
    """Raise the flag for this process, or refuse because another updater already did.

    The lock comes first and the JSON second: the lock is held by the kernel for as long as this
    process lives, which closes the window an `exists?` → `write` pair leaves open (two updaters
    could both find the file stale, each delete the other's and each believe it holds the flag).
    The JSON is checked too, because an updater from before the lock existed holds only that.
    """
    held = active()
    if held is not None:
        raise MaintenanceHeld(f"maintenance flag held by pid {held.pid} ({held.reason})")
    _take_lock()

    flag = MaintenanceFlag(
        pid=os.getpid(),
        started_at=_utc_now(),
        reason=reason,
        start_time=process_start_time(os.getpid()),
    )
    path = flag_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(flag.as_json()), encoding="utf-8")
    return flag


def end() -> None:
    """Lower the flag and release the lock; a missing file is success."""
    global _held_lock

    flag_path().unlink(missing_ok=True)
    if _held_lock is not None:
        _held_lock.close()
        _held_lock = None


def _take_lock() -> None:
    global _held_lock

    if fcntl is None:  # pragma: no cover — Windows: the JSON above is the only guard there
        return
    path = lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as taken:
        handle.close()
        raise MaintenanceHeld("maintenance lock is held by another updater") from taken
    _held_lock = handle


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


__all__ = [
    "MAX_AGE_SECONDS",
    "MaintenanceFlag",
    "MaintenanceHeld",
    "active",
    "begin",
    "end",
    "flag_path",
    "is_active",
    "lock_path",
    "process_is_updater",
    "read",
]
