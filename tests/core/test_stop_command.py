"""`app.py stop`: план печатается до сигналов, отказы становятся кодами выхода.

Команда — тонкая обёртка над тем же слоем, что гасит установку внутри обновления, поэтому
проверяется её собственная половина: что план показан, что сухой прогон ничего не подаёт, что
каждый отказ доезжает до кода выхода, а не превращается в трейсбек у того, кто звал `./run.sh stop`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.update import sequence
from src.core.update.sequence import (
    EXIT_OK,
    EXIT_STOP_FAILED,
    EXIT_UNREGISTERED,
    EXIT_UNSUPPORTED_PLATFORM,
    stop_command,
)
from src.core.update.stop import (
    ForeignProcesses,
    OwnIdentity,
    ProcessesSurvived,
    StopPlan,
    StopTarget,
    UnregisteredProcesses,
    UpdaterInsideInstall,
)

CHECKOUT = Path("/tmp/install")
BACKEND_PID = 4242


def _plan() -> StopPlan:
    return StopPlan(
        checkout=CHECKOUT,
        own=OwnIdentity(pid=1, pgid=1),
        singles=(
            StopTarget(
                pid=BACKEND_PID,
                start_time=1.0,
                command_line="src/app.py --backend --worker",
                matched_as="recorded",
            ),
        ),
    )


@pytest.fixture
def planned(monkeypatch):
    """Подменить планирование живой машины; вернуть журнал переданных в него параметров."""
    asked: list[dict] = []

    def fake_plan_live_stop(checkout, *, stop_unregistered=False):
        asked.append({"checkout": checkout, "stop_unregistered": stop_unregistered})
        return _plan()

    monkeypatch.setattr(sequence, "plan_live_stop", fake_plan_live_stop)
    return asked


@pytest.fixture
def signalled(monkeypatch):
    """Подменить подачу сигналов; вернуть журнал планов, которые до неё дошли."""
    signalled_plans: list[StopPlan] = []

    def fake_execute_stop(plan, **kwargs):
        signalled_plans.append(plan)
        return []

    monkeypatch.setattr(sequence, "execute_stop", fake_execute_stop)
    return signalled_plans


def _refuse_with(monkeypatch, refusal: Exception) -> None:
    def refuse(plan, **kwargs):
        raise refusal

    monkeypatch.setattr(sequence, "execute_stop", refuse)


def _forbid_signals(monkeypatch) -> None:
    """Подача сигналов в этом тесте — провал, а не один из путей."""

    def forbidden(plan, **kwargs):
        raise AssertionError("сигнал подан там, где его быть не должно")

    monkeypatch.setattr(sequence, "execute_stop", forbidden)


@pytest.mark.pure
def test_the_plan_is_printed_and_then_signalled(planned, signalled, capsys):
    assert stop_command() == EXIT_OK

    assert len(signalled) == 1
    printed = capsys.readouterr().out
    assert str(BACKEND_PID) in printed
    assert str(CHECKOUT) in printed


@pytest.mark.pure
def test_a_dry_run_prints_the_plan_and_signals_nothing(planned, monkeypatch, capsys):
    """Сухой прогон обязан быть безопасным ответом на вопрос «а что ты погасишь»."""
    _forbid_signals(monkeypatch)

    assert stop_command(dry_run=True) == EXIT_OK
    assert str(BACKEND_PID) in capsys.readouterr().out


@pytest.mark.pure
def test_stop_unregistered_reaches_the_planner(planned, signalled):
    """Флаг меняет именно план, а не поведение сигналов: гасить без записи или отказаться —
    решение принимается при планировании."""
    stop_command(stop_unregistered=True)

    assert planned[-1]["stop_unregistered"] is True


@pytest.mark.pure
def test_processes_without_a_record_end_as_exit_10(planned, monkeypatch, capsys):
    """Тот же код, что и у обновления: незарегистрированные процессы — отказ, а не тихое гашение
    по косвенным уликам."""
    _refuse_with(monkeypatch, UnregisteredProcesses("pid 4242 looks like this install"))

    assert stop_command() == EXIT_UNREGISTERED
    assert "refusing to stop" in capsys.readouterr().out


@pytest.mark.pure
@pytest.mark.parametrize(
    "refusal",
    [
        ProcessesSurvived("still alive after TERM and KILL"),
        ForeignProcesses("pid 4242 belongs to another user"),
        UpdaterInsideInstall("the updater shares process group 7 with the install"),
    ],
    ids=["survived", "another user", "own group"],
)
def test_an_install_that_did_not_stop_is_never_reported_as_stopped(
    planned, monkeypatch, capsys, refusal
):
    _refuse_with(monkeypatch, refusal)

    assert stop_command() == EXIT_STOP_FAILED
    assert "refusing to stop" in capsys.readouterr().out


@pytest.mark.pure
def test_windows_is_refused_with_a_message_not_a_traceback(planned, monkeypatch, capsys):
    """Гашение построено на группах процессов POSIX; на Windows команда обязана сказать это
    словами — трейсбек из глубины не подскажет, что делать."""
    monkeypatch.setattr(sequence.sys, "platform", "win32")

    assert stop_command() == EXIT_UNSUPPORTED_PLATFORM
    assert "Windows" in capsys.readouterr().out
    assert planned == []
