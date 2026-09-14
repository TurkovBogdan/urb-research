"""`src/app.py::main` — гейт запуска под флагом обслуживания и его область.

Запуск процесса (в том числе `--mcp-stdio`) под поднятым флагом отклоняется, подкоманды —
нет: апдейтер сам гоняет `migrate upgrade` при поднятом флаге, а упавшая миграция флаг не
опускает, и повтор обязан пройти.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import app
from src.core import maintenance


@pytest.fixture
def update_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> maintenance.MaintenanceFlag:
    """Поднятый флаг во ВРЕМЕННОМ каталоге: живой флаг в настоящем `runtime/` запер бы
    запуск всего на этой машине, включая MCP-шимы соседних сессий."""
    monkeypatch.setattr(maintenance, "project_root", lambda: tmp_path)
    monkeypatch.setattr(maintenance, "process_is_updater", lambda pid: True)
    return maintenance.begin("update to head")


@pytest.mark.pure
def test_process_launch_is_the_no_subcommand_path():
    launch = argparse.Namespace(command=None)

    assert app._launches_a_process(launch) is True


@pytest.mark.pure
@pytest.mark.parametrize("subcommand", ["migrate", "update"])
def test_subcommands_are_exempt_from_the_gate(subcommand: str):
    assert app._launches_a_process(argparse.Namespace(command=subcommand)) is False


@pytest.mark.pure
def test_bare_launch_refuses_while_the_flag_is_up(update_in_progress, capsys):
    exit_code = app.main([])

    assert exit_code == 1
    refusal = capsys.readouterr().err
    assert "обновление" in refusal
    assert str(update_in_progress.pid) in refusal
    assert "update to head" in refusal


@pytest.mark.pure
def test_mcp_stdio_launch_refuses_while_the_flag_is_up(
    update_in_progress, monkeypatch: pytest.MonkeyPatch, capsys
):
    from src.apps.app import mcp_stdio

    started = []
    monkeypatch.setattr(mcp_stdio, "run_mcp_stdio", lambda config: started.append(config))

    assert app.main(["--mcp-stdio"]) == 1
    assert started == []
    assert "обновление" in capsys.readouterr().err


@pytest.mark.pure
def test_migrate_runs_while_the_flag_is_up(update_in_progress, monkeypatch: pytest.MonkeyPatch):
    """Гейт на `migrate` запер бы обновление изнутри: шаг 8 накатывает миграции под флагом."""
    actions = []

    async def _record(action: str) -> int:
        actions.append(action)
        return 0

    monkeypatch.setattr(app, "_run_migrate", _record)

    assert app.main(["migrate", "upgrade"]) == 0
    assert actions == ["upgrade"]


@pytest.mark.pure
def test_launch_is_not_gated_without_a_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(maintenance, "project_root", lambda: tmp_path)

    assert app._maintenance_refusal() is None


@pytest.mark.pure
def test_a_dead_updater_does_not_gate_the_launch(
    update_in_progress, monkeypatch: pytest.MonkeyPatch
):
    """Liveness is the pid plus its start time: a flag whose updater died stops gating at once,
    however recent the file is."""
    monkeypatch.setattr(maintenance, "process_is_running", lambda pid, start_time=None: False)

    assert app._maintenance_refusal() is None


# ── the process registry: what a launch records about itself ─────────────────

@pytest.mark.pure
def test_a_launched_role_is_recorded_and_the_record_is_removed_afterwards(
    monkeypatch: pytest.MonkeyPatch,
):
    """The updater stops the install from these records, so a process that runs without one is a
    process the update will refuse to work around."""
    from src.core import process_registry

    recorded: list[str] = []
    monkeypatch.setattr(
        app,
        "_run_the_role",
        lambda config, args: recorded.extend(
            record.role for record in process_registry.read_records()
        ),
    )

    app.main(["--backend", "--no-worker"])

    assert recorded == [process_registry.ROLE_BACKEND]
    assert process_registry.read_records() == []


@pytest.mark.pure
def test_the_stdio_shim_records_nothing(monkeypatch: pytest.MonkeyPatch):
    """The shim is the client's process, never a target — and it refuses to spawn under the flag."""
    from src.apps.app import mcp_stdio
    from src.core import process_registry

    monkeypatch.setattr(mcp_stdio, "run_mcp_stdio", lambda config: None)

    app.main(["--mcp-stdio"])

    assert process_registry.read_records() == []


@pytest.mark.pure
def test_a_launch_refused_by_the_flag_records_nothing(update_in_progress):
    from src.core import process_registry

    assert app.main([]) == 1
    assert process_registry.read_records() == []
