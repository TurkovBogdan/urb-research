"""Maintenance flag: a kernel-held lock for exclusion, identity by pid + start time for liveness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psutil
import pytest

from src.core import maintenance
from src.core.maintenance import MaintenanceFlag, MaintenanceHeld

HOLDS_THE_LOCK = (
    "import fcntl, sys, time\n"
    "handle = open(sys.argv[1], 'a+')\n"
    "fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "print('locked', flush=True)\n"
    "time.sleep(60)\n"
)


@pytest.fixture
def flag_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Move the flag out of the real checkout — tests must not write into `runtime/`."""
    monkeypatch.setattr(maintenance, "project_root", lambda: tmp_path)
    try:
        yield tmp_path
    finally:
        maintenance.end()


@pytest.fixture
def live_updater(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend the recorded pid is a running `src/app.py update` (this process is pytest)."""
    monkeypatch.setattr(maintenance, "process_is_updater", lambda pid: True)


def a_dead_pid() -> int:
    """Asked of the system, not of `/proc`: the flag is read on whatever the operator runs."""
    for candidate in range(4_000_000, 4_100_000):
        if not psutil.pid_exists(candidate):
            return candidate
    raise AssertionError("no free pid found")


def write_flag(
    pid: int,
    *,
    age: timedelta = timedelta(0),
    reason: str = "update",
    start_time: float | None = None,
) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    flag = MaintenanceFlag(pid=pid, started_at=now - age, reason=reason, start_time=start_time)
    maintenance.flag_path().parent.mkdir(parents=True, exist_ok=True)
    maintenance.flag_path().write_text(json.dumps(flag.as_json()), encoding="utf-8")


def own_start_time() -> float:
    return psutil.Process(os.getpid()).create_time()


@pytest.mark.pure
def test_flag_path_ignores_app_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "prod")
    path_under_prod = maintenance.flag_path()
    monkeypatch.delenv("APP_ENV", raising=False)

    assert maintenance.flag_path() == path_under_prod
    assert path_under_prod.parent.name == "runtime"
    assert maintenance.lock_path().parent == path_under_prod.parent


@pytest.mark.pure
def test_missing_file_is_inactive(flag_root: Path):
    assert maintenance.read() is None
    assert maintenance.is_active() is False


@pytest.mark.pure
def test_dead_pid_is_inactive(flag_root: Path):
    write_flag(a_dead_pid(), start_time=own_start_time())

    assert maintenance.read() is not None
    assert maintenance.is_active() is False


@pytest.mark.pure
def test_a_pid_whose_process_started_at_another_time_is_inactive(flag_root: Path):
    """Pid reuse after a reboot: the number is alive and is not the updater that wrote the flag."""
    write_flag(os.getpid(), start_time=1.0)

    assert maintenance.is_active() is False


@pytest.mark.pure
def test_the_live_process_that_wrote_the_flag_holds_it(flag_root: Path):
    write_flag(os.getpid(), start_time=own_start_time())

    assert maintenance.is_active() is True


@pytest.mark.pure
def test_a_flag_from_before_start_times_falls_back_to_the_argv_check(flag_root: Path):
    """An update in progress while this very change ships wrote the old shape; reading it as
    inactive would let the shim boot a backend onto a half-rewritten tree."""
    write_flag(os.getpid())

    assert maintenance.is_active() is False

    with pytest.MonkeyPatch.context() as looks_like_an_updater:
        looks_like_an_updater.setattr(maintenance, "process_is_updater", lambda pid: True)
        assert maintenance.is_active() is True


@pytest.mark.pure
def test_begin_clears_a_stale_file(flag_root: Path):
    write_flag(a_dead_pid(), reason="crashed updater", start_time=own_start_time())

    flag = maintenance.begin("update to head")

    assert flag.pid == os.getpid()
    stored = maintenance.read()
    assert stored is not None
    assert stored.pid == os.getpid()
    assert stored.reason == "update to head"


@pytest.mark.pure
def test_stored_flag_carries_the_identity_of_its_updater(flag_root: Path):
    maintenance.begin("update")

    payload = json.loads(maintenance.flag_path().read_text(encoding="utf-8"))
    assert set(payload) == {"pid", "started_at", "reason", "start_time"}
    assert payload["start_time"] == pytest.approx(own_start_time())
    assert "T" not in payload["started_at"]
    assert len(payload["started_at"]) == len("2026-09-11 12:34:56")


@pytest.mark.pure
def test_clock_jump_forward_does_not_expire_a_live_updater(flag_root: Path):
    write_flag(os.getpid(), age=timedelta(minutes=59), start_time=own_start_time())

    assert maintenance.is_active() is True


@pytest.mark.pure
def test_age_bound_releases_a_pid_that_outlived_its_file(flag_root: Path):
    write_flag(
        os.getpid(),
        age=timedelta(seconds=maintenance.MAX_AGE_SECONDS + 1),
        start_time=own_start_time(),
    )

    assert maintenance.is_active() is False


@pytest.mark.pure
def test_second_begin_raises(flag_root: Path):
    maintenance.begin("first")

    with pytest.raises(MaintenanceHeld):
        maintenance.begin("second")


@pytest.mark.pure
def test_a_lock_held_by_another_process_refuses_even_without_a_flag_file(flag_root: Path):
    """The race a file cannot close: two updaters both find no flag, and each writes one. The lock
    is taken by the kernel, so only one of them proceeds."""
    maintenance.lock_path().parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDS_THE_LOCK, str(maintenance.lock_path())],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "locked"
        assert maintenance.read() is None

        with pytest.raises(MaintenanceHeld):
            maintenance.begin("second updater")
    finally:
        holder.kill()
        holder.wait()
        holder.stdout.close()

    assert maintenance.begin("after the holder died").pid == os.getpid()


@pytest.mark.pure
def test_end_is_idempotent(flag_root: Path):
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
