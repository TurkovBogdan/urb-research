"""Maintenance flag: liveness by pid, not by wall clock."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.core import maintenance
from src.core.maintenance import MaintenanceFlag, MaintenanceHeld


@pytest.fixture
def flag_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Move the flag out of the real checkout — tests must not write into `runtime/`."""
    monkeypatch.setattr(maintenance, "project_root", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def live_updater(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend the recorded pid is a running `src/app.py update` (this process is pytest)."""
    monkeypatch.setattr(maintenance, "process_is_updater", lambda pid: True)


def a_dead_pid() -> int:
    for candidate in range(4_000_000, 4_100_000):
        if not Path(f"/proc/{candidate}").exists():
            return candidate
    raise AssertionError("no free pid found")


def write_flag(pid: int, *, age: timedelta = timedelta(0), reason: str = "update") -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    flag = MaintenanceFlag(pid=pid, started_at=now - age, reason=reason)
    maintenance.flag_path().parent.mkdir(parents=True, exist_ok=True)
    maintenance.flag_path().write_text(json.dumps(flag.as_json()), encoding="utf-8")


@pytest.mark.pure
def test_flag_path_ignores_app_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "prod")
    path_under_prod = maintenance.flag_path()
    monkeypatch.delenv("APP_ENV", raising=False)

    assert maintenance.flag_path() == path_under_prod
    assert path_under_prod.parent.name == "runtime"


@pytest.mark.pure
def test_missing_file_is_inactive(flag_root: Path):
    assert maintenance.read() is None
    assert maintenance.is_active() is False


@pytest.mark.pure
def test_dead_pid_is_inactive(flag_root: Path):
    write_flag(a_dead_pid())

    assert maintenance.read() is not None
    assert maintenance.is_active() is False


@pytest.mark.pure
def test_live_pid_that_is_not_an_updater_is_inactive(flag_root: Path):
    write_flag(os.getpid())

    assert maintenance.is_active() is False


@pytest.mark.pure
def test_begin_clears_a_stale_file(flag_root: Path):
    write_flag(a_dead_pid(), reason="crashed updater")

    flag = maintenance.begin("update to head")

    assert flag.pid == os.getpid()
    stored = maintenance.read()
    assert stored is not None
    assert stored.pid == os.getpid()
    assert stored.reason == "update to head"


@pytest.mark.pure
def test_stored_timestamp_is_sql_format(flag_root: Path):
    maintenance.begin("update")

    payload = json.loads(maintenance.flag_path().read_text(encoding="utf-8"))
    assert set(payload) == {"pid", "started_at", "reason"}
    assert "T" not in payload["started_at"]
    assert len(payload["started_at"]) == len("2026-09-11 12:34:56")


@pytest.mark.pure
def test_clock_jump_forward_does_not_expire_a_live_updater(flag_root: Path, live_updater: None):
    write_flag(os.getpid(), age=timedelta(minutes=59))

    assert maintenance.is_active() is True


@pytest.mark.pure
def test_age_bound_releases_a_pid_that_outlived_its_file(flag_root: Path, live_updater: None):
    write_flag(os.getpid(), age=timedelta(seconds=maintenance.MAX_AGE_SECONDS + 1))

    assert maintenance.is_active() is False


@pytest.mark.pure
def test_second_begin_raises(flag_root: Path, live_updater: None):
    maintenance.begin("first")

    with pytest.raises(MaintenanceHeld):
        maintenance.begin("second")


@pytest.mark.pure
def test_end_is_idempotent(flag_root: Path, live_updater: None):
    maintenance.begin("update")

    maintenance.end()
    maintenance.end()

    assert maintenance.is_active() is False
    assert not maintenance.flag_path().exists()


@pytest.mark.pure
def test_corrupt_file_reads_as_absent(flag_root: Path):
    maintenance.flag_path().parent.mkdir(parents=True, exist_ok=True)
    maintenance.flag_path().write_text("{half-written", encoding="utf-8")

    assert maintenance.read() is None
    assert maintenance.is_active() is False


@pytest.mark.pure
def test_process_is_updater_rejects_a_dead_pid():
    assert maintenance.process_is_updater(a_dead_pid()) is False


@pytest.mark.pure
def test_process_is_updater_rejects_a_live_non_updater():
    assert maintenance.process_is_updater(os.getpid()) is False
