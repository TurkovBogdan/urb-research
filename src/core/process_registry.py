"""What this install is running, as recorded by the processes themselves.

One file per process at `<project>/runtime/processes/<pid>.json`, written at boot and removed on a
clean exit. The updater reads these records instead of reconstructing the install from the process
table: `cwd` and `argv` are readable only for one's own user on macOS and need a PEB read on
Windows, and a process may rewrite its own `argv` — so evidence gathered afterwards degrades from
OS to OS, while a record written at the start does not. Why this replaced the hunt, and what the
records are used for: `AGENTS/docs/platform/update.md`.

The directory is at the project root, not under `runtime/<APP_ENV>/`, for the same reason as
`runtime/maintenance.json`: the writer's `APP_ENV` and the reader's may differ, and a per-profile
path would let the two resolve different directories. Imports stay at the stdlib, `psutil` and the
process table — a record is written before the app exists and read by an updater whose venv is
about to be replaced.
"""

from __future__ import annotations

import enum
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.app_path import project_root
from src.core.process_table import Liveness, process_liveness, process_start_time

if TYPE_CHECKING:
    from src.core.config import Config

SCHEMA = 1

ROLE_BACKEND = "backend"
ROLE_WORKER = "worker"
ROLE_BACKEND_WORKER = "backend+worker"

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class RecordState(enum.Enum):
    """What a record turned out to describe when it was checked against the live machine."""

    VERIFIED = "verified"
    STALE = "stale"
    FOREIGN = "foreign"
    OTHER_CHECKOUT = "other checkout"


@dataclass(frozen=True)
class ProcessRecord:
    """A process of this install, as it described itself at boot.

    `pid` alone is not an identity — pids are reused after a crash or a reboot — so every check
    pairs it with `start_time`. `pgid`/`sid` are None on a platform without process groups, which
    is also a platform where no group can be signalled.
    """

    pid: int
    start_time: float
    ppid: int
    pgid: int | None
    sid: int | None
    role: str
    hot_reload: bool
    port: int | None
    app_env: str
    checkout: str
    argv: tuple[str, ...]
    written_at: str

    @property
    def serves_http(self) -> bool:
        return self.role in (ROLE_BACKEND, ROLE_BACKEND_WORKER)

    def as_json(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "pid": self.pid,
            "start_time": self.start_time,
            "ppid": self.ppid,
            "pgid": self.pgid,
            "sid": self.sid,
            "role": self.role,
            "hot_reload": self.hot_reload,
            "port": self.port,
            "app_env": self.app_env,
            "checkout": self.checkout,
            "argv": list(self.argv),
            "written_at": self.written_at,
        }

    @staticmethod
    def from_json(payload: dict[str, object]) -> "ProcessRecord":
        return ProcessRecord(
            pid=int(payload["pid"]),  # type: ignore[arg-type]
            start_time=float(payload["start_time"]),  # type: ignore[arg-type]
            ppid=int(payload.get("ppid", 0)),  # type: ignore[arg-type]
            pgid=_optional_int(payload.get("pgid")),
            sid=_optional_int(payload.get("sid")),
            role=str(payload.get("role", "")),
            hot_reload=bool(payload.get("hot_reload", False)),
            port=_optional_int(payload.get("port")),
            app_env=str(payload.get("app_env", "")),
            checkout=str(payload.get("checkout", "")),
            argv=tuple(str(token) for token in payload.get("argv", ()) or ()),
            written_at=str(payload.get("written_at", "")),
        )

    def describe(self) -> str:
        group = f"group {self.pgid}" if self.pgid is not None else "no process group"
        port = f", port {self.port}" if self.port is not None else ""
        return f"pid {self.pid} [{self.role}, {self.app_env}, {group}{port}]: {self.command_line}"

    @property
    def command_line(self) -> str:
        return " ".join(self.argv)


def registry_dir() -> Path:
    return project_root() / "runtime" / "processes"


def record_path(pid: int) -> Path:
    return registry_dir() / f"{pid}.json"


def announce(config: "Config") -> ProcessRecord | None:
    """Record this process as one of the install's, and drop the records of processes that died.

    None when the machine will not say when this process started: without that, the record could
    not be told from a stranger who inherits the pid later, and a record that cannot be verified is
    worse than none — the updater would refuse the install it is supposed to stop.
    """
    started_at = process_start_time(os.getpid())
    if started_at is None:  # pragma: no cover — psutil has no answer for its own process
        return None

    forget_dead_records()
    record = ProcessRecord(
        pid=os.getpid(),
        start_time=started_at,
        ppid=os.getppid(),
        pgid=_own_process_group(),
        sid=_own_session(),
        role=role_of(config),
        hot_reload=config.server_hot_reload,
        port=config.server_port if config.server_enabled else None,
        app_env=config.app_env,
        checkout=str(project_root()),
        argv=tuple(sys.argv),
        written_at=_utc_now(),
    )
    _write(record)
    return record


def withdraw(pid: int | None = None) -> None:
    """Remove one record; a missing file is success (an `execv` restart rewrites its own)."""
    record_path(os.getpid() if pid is None else pid).unlink(missing_ok=True)


def read_records() -> list[ProcessRecord]:
    """Every readable record, oldest pid first; a torn or foreign file is skipped, not an error."""
    try:
        files = sorted(registry_dir().glob("*.json"))
    except OSError:
        return []
    records = (_read(path) for path in files)
    return [record for record in records if record is not None]


def verify(record: ProcessRecord) -> RecordState:
    """What the record describes right now — the only gate between a record and a signal."""
    if Path(record.checkout) != project_root():
        return RecordState.OTHER_CHECKOUT
    liveness = process_liveness(record.pid, start_time=record.start_time)
    if liveness is Liveness.FOREIGN:
        return RecordState.FOREIGN
    return RecordState.VERIFIED if liveness is Liveness.ALIVE else RecordState.STALE


def forget_dead_records() -> None:
    """Drop the records of processes that are gone, so the directory cannot grow without bound.

    A SIGKILLed process, a reboot and a `watchfiles` restart all leave a record behind; only a
    record whose pid is verifiably not that process any more is removed here.
    """
    for record in read_records():
        if verify(record) is RecordState.STALE:
            withdraw(record.pid)


def role_of(config: "Config") -> str:
    if config.server_enabled and config.worker_enabled:
        return ROLE_BACKEND_WORKER
    return ROLE_BACKEND if config.server_enabled else ROLE_WORKER


def _write(record: ProcessRecord) -> None:
    """Atomically: a torn record must read as absent, never as a different process."""
    path = record_path(record.pid)
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_suffix(".json.partial")
    scratch.write_text(json.dumps(record.as_json()), encoding="utf-8")
    os.replace(scratch, path)


def _read(path: Path) -> ProcessRecord | None:
    try:
        return ProcessRecord.from_json(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _own_process_group() -> int | None:
    return os.getpgrp() if hasattr(os, "getpgrp") else None


def _own_session() -> int | None:
    return os.getsid(0) if hasattr(os, "getsid") else None


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)  # type: ignore[arg-type]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0).strftime(
        _TIMESTAMP_FORMAT
    )


__all__ = [
    "ROLE_BACKEND",
    "ROLE_BACKEND_WORKER",
    "ROLE_WORKER",
    "SCHEMA",
    "ProcessRecord",
    "RecordState",
    "announce",
    "forget_dead_records",
    "read_records",
    "record_path",
    "registry_dir",
    "role_of",
    "verify",
    "withdraw",
]
