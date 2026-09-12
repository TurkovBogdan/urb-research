"""The process registry: what a process writes about itself, and when that record stops counting.

The registry is moved into a `tmp_path` for every test — a suite that wrote into the real
`runtime/processes/` would describe the developer's own backends to the next updater that runs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import psutil
import pytest

from src.core import process_registry
from src.core.config import Config
from src.core.process_registry import (
    ROLE_BACKEND,
    ROLE_BACKEND_WORKER,
    ROLE_WORKER,
    ProcessRecord,
    RecordState,
    announce,
    read_records,
    record_path,
    registry_dir,
    verify,
    withdraw,
)

REAPED = "import sys\nsys.exit(0)\n"


@pytest.fixture
def registry_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(process_registry, "project_root", lambda: tmp_path)
    return tmp_path


def install_config(**over) -> Config:
    settings = dict(server_enabled=True, worker_enabled=True, server_port=12200)
    return Config(**{**settings, **over})


def a_dead_pid() -> int:
    child = subprocess.Popen([sys.executable, "-c", REAPED])
    child.wait()
    return child.pid


@pytest.mark.pure
def test_registry_path_ignores_app_env(monkeypatch: pytest.MonkeyPatch):
    """The writer's profile and the updater's may differ; a per-profile path would let the two
    resolve different directories — the same trap the maintenance flag avoids."""
    monkeypatch.setenv("APP_ENV", "prod")
    path_under_prod = registry_dir()
    monkeypatch.delenv("APP_ENV", raising=False)

    assert registry_dir() == path_under_prod
    assert path_under_prod.parent.name == "runtime"


@pytest.mark.pure
def test_announce_writes_this_process_and_withdraw_removes_it(registry_root: Path):
    record = announce(install_config())

    assert record is not None
    assert record.pid == os.getpid()
    assert record.role == ROLE_BACKEND_WORKER
    assert record.port == 12200
    assert record.checkout == str(registry_root)
    assert record_path(os.getpid()).exists()

    withdraw()

    assert read_records() == []


@pytest.mark.pure
def test_the_record_is_readable_json_with_a_schema_and_a_sql_timestamp(registry_root: Path):
    announce(install_config())

    payload = json.loads(record_path(os.getpid()).read_text(encoding="utf-8"))
    assert payload["schema"] == process_registry.SCHEMA
    assert payload["start_time"] == pytest.approx(psutil.Process(os.getpid()).create_time())
    assert "T" not in payload["written_at"]


@pytest.mark.pure
@pytest.mark.parametrize(
    ("server", "worker", "role"),
    [(True, True, ROLE_BACKEND_WORKER), (True, False, ROLE_BACKEND), (False, True, ROLE_WORKER)],
)
def test_the_role_is_the_surfaces_the_process_actually_serves(
    registry_root: Path, server: bool, worker: bool, role: str
):
    record = announce(install_config(server_enabled=server, worker_enabled=worker))

    assert record is not None
    assert record.role == role
    assert record.port == (12200 if server else None)


@pytest.mark.pure
def test_announcing_twice_overwrites_instead_of_duplicating(registry_root: Path):
    """`core_setup`'s restart is `os.execv`: same pid, same start time, `main()` entered again."""
    announce(install_config())
    announce(install_config(worker_enabled=False))

    records = read_records()
    assert [record.pid for record in records] == [os.getpid()]
    assert records[0].role == ROLE_BACKEND


@pytest.mark.pure
def test_verify_accepts_this_process_and_rejects_a_reused_pid(registry_root: Path):
    record = announce(install_config())
    assert record is not None

    assert verify(record) is RecordState.VERIFIED
    assert verify(replace(record, start_time=1.0)) is RecordState.STALE


@pytest.mark.pure
def test_verify_calls_a_dead_pid_stale(registry_root: Path):
    record = announce(install_config())
    assert record is not None

    assert verify(replace(record, pid=a_dead_pid())) is RecordState.STALE


@pytest.mark.pure
def test_verify_calls_another_users_process_foreign(
    registry_root: Path, monkeypatch: pytest.MonkeyPatch
):
    """On macOS this is the install running under another account: unreadable and unstoppable, so
    the update must refuse rather than migrate beside it."""
    record = announce(install_config())
    assert record is not None
    monkeypatch.setattr(
        psutil.Process, "status", lambda self: (_ for _ in ()).throw(psutil.AccessDenied(self.pid))
    )

    assert verify(record) is RecordState.FOREIGN


@pytest.mark.pure
def test_a_record_left_by_another_checkout_is_not_ours(registry_root: Path):
    """A `runtime/` copied from another clone would otherwise hand the updater someone else's
    processes to signal."""
    record = announce(install_config())
    assert record is not None

    assert verify(replace(record, checkout="/srv/somewhere-else")) is RecordState.OTHER_CHECKOUT


@pytest.mark.pure
def test_announce_drops_the_records_of_processes_that_died(registry_root: Path):
    """SIGKILL, a kernel panic and a `watchfiles` restart all leave a record behind; the next boot
    is what cleans up, so the directory cannot grow without bound."""
    dead = ProcessRecord(
        pid=a_dead_pid(),
        start_time=1.0,
        ppid=1,
        pgid=None,
        sid=None,
        role=ROLE_BACKEND,
        hot_reload=False,
        port=12200,
        app_env="prod",
        checkout=str(registry_root),
        argv=("python", "src/app.py", "--backend"),
        written_at="2026-09-13 10:00:00",
    )
    registry_dir().mkdir(parents=True, exist_ok=True)
    record_path(dead.pid).write_text(json.dumps(dead.as_json()), encoding="utf-8")

    announce(install_config())

    assert [record.pid for record in read_records()] == [os.getpid()]


@pytest.mark.pure
def test_a_torn_record_reads_as_absent(registry_root: Path):
    registry_dir().mkdir(parents=True, exist_ok=True)
    record_path(4242).write_text("{half-written", encoding="utf-8")

    assert read_records() == []


@pytest.mark.pure
def test_no_registry_directory_is_no_records(registry_root: Path):
    assert read_records() == []
    withdraw(4242)
