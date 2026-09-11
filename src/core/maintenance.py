"""Maintenance flag — «an update is in progress, do not launch anything».

A JSON file at `<project>/runtime/maintenance.json`; active while its pid is a live updater and
the file is younger than `MAX_AGE_SECONDS`. `begin` creates it exclusively (`MaintenanceHeld`
when another updater got there first), `end` removes it. Stdlib only: the flag is read before
`Config()` and before any database import. Why the path and the liveness rule are what they
are: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.core.app_path import project_root

MAX_AGE_SECONDS = 3600

# An updater is `src/app.py update`; both markers must be present, so a plain backend that
# happens to reuse the pid is not mistaken for one.
UPDATER_ARGV_MARKERS = ("app.py", "update")

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class MaintenanceHeld(RuntimeError):
    """Another updater holds the flag."""


@dataclass(frozen=True)
class MaintenanceFlag:
    pid: int
    started_at: datetime
    reason: str

    def as_json(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "started_at": self.started_at.strftime(_TIMESTAMP_FORMAT),
            "reason": self.reason,
        }

    @staticmethod
    def from_json(payload: dict[str, object]) -> "MaintenanceFlag":
        return MaintenanceFlag(
            pid=int(payload["pid"]),  # type: ignore[arg-type]
            started_at=datetime.strptime(str(payload["started_at"]), _TIMESTAMP_FORMAT),
            reason=str(payload.get("reason", "")),
        )

    def age_seconds(self, now: datetime | None = None) -> float:
        return ((now or _utc_now()) - self.started_at).total_seconds()

    def is_live(self, now: datetime | None = None) -> bool:
        within_age_bound = self.age_seconds(now) < MAX_AGE_SECONDS
        return within_age_bound and process_is_updater(self.pid)

    def describe(self) -> str:
        started = self.started_at.strftime(_TIMESTAMP_FORMAT)
        return f"pid {self.pid}, since {started}: {self.reason}"


def flag_path() -> Path:
    return project_root() / "runtime" / "maintenance.json"


def process_is_updater(pid: int) -> bool:
    """The pid is alive AND its argv still looks like `src/app.py update` (pid-reuse guard)."""
    if not _process_is_alive(pid):
        return False
    argv = _process_argv(pid)
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
    """Raise the flag for this process. An inactive (stale) file is cleared first.

    The exclusive creation is the mutual exclusion: a racing updater that got there first loses
    the `open(..., "x")` and is told the flag is held.
    """
    if is_active():
        held = read()
        raise MaintenanceHeld(
            f"maintenance flag held by pid {held.pid if held else '?'} "
            f"({held.reason if held else 'unknown reason'})"
        )

    path = flag_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    flag = MaintenanceFlag(pid=os.getpid(), started_at=_utc_now(), reason=reason)
    try:
        with open(path, "x", encoding="utf-8") as handle:
            json.dump(flag.as_json(), handle)
    except FileExistsError as race:
        raise MaintenanceHeld("maintenance flag was raised by another updater") from race
    return flag


def end() -> None:
    """Lower the flag; a missing file is success."""
    flag_path().unlink(missing_ok=True)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _process_argv(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
    except OSError:
        return None


__all__ = [
    "MAX_AGE_SECONDS",
    "MaintenanceFlag",
    "MaintenanceHeld",
    "active",
    "begin",
    "end",
    "flag_path",
    "is_active",
    "process_is_updater",
    "read",
]
