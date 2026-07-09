"""HTTP-API раздела «Задачи» модуля core_monitoring (/internal/tasks)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.crud import tasks as crud_tasks
from src.core.crud import tasks_logs as crud_tasks_logs
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.core.models.tasks import CoreTaskLogLevel
from src.core.scheduler.registry import get_registry
from src.modules.core_monitoring.api import internal_router

_MODULE = "test_monitoring"
_CODE = "demo"


async def _noop_handler(ctx) -> None:  # noqa: ANN001 — сигнатура хендлера задачи
    return None


@pytest.fixture(autouse=True)
def register_demo_task():
    registry = get_registry()
    if registry.get(_MODULE, _CODE) is None:
        registry.register(
            module=_MODULE,
            code=_CODE,
            name="Demo",
            description="Демо-задача для теста мониторинга",
            schedule="* * * * *",
            handler=_noop_handler,
            ttl=60,
            enabled=True,
        )


@pytest.fixture
async def app(config: Config):
    engine = await init_database(config)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    fastapi_app = FastAPI()
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(internal_router, prefix="/internal")
    try:
        yield fastapi_app
    finally:
        await close_database()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.db
async def test_list_tasks_includes_registered_task_with_zero_stats(client):
    r = await client.get("/internal/tasks")
    assert r.status_code == 200
    tasks = {(t["module"], t["code"]): t for t in r.json()}
    demo = tasks[(_MODULE, _CODE)]
    assert demo["name"] == "Demo"
    assert demo["schedule"] == "* * * * *"
    assert demo["stats_24h"] == {"total": 0, "success": 0, "error": 0, "running": 0}


@pytest.mark.db
async def test_get_task_missing_returns_404(client):
    r = await client.get("/internal/tasks/nope/nope")
    assert r.status_code == 404


@pytest.mark.db
async def test_runs_and_logs_roundtrip(client):
    task_id = await crud_tasks.create_running(module=_MODULE, code=_CODE)
    assert task_id is not None
    await crud_tasks_logs.create(
        task_id=task_id, level=CoreTaskLogLevel.info, message="hello world"
    )
    await crud_tasks.finalize_success(task_id)

    runs = await client.get(f"/internal/tasks/{_MODULE}/{_CODE}/runs")
    assert runs.status_code == 200
    body = runs.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "success"

    logs = await client.get(f"/internal/tasks/{_MODULE}/{_CODE}/runs/{task_id}/logs")
    assert logs.status_code == 200
    entries = logs.json()
    assert [e["message"] for e in entries] == ["hello world"]
    assert entries[0]["level"] == "info"


@pytest.mark.db
async def test_runs_status_filter(client):
    ok = await crud_tasks.create_running(module=_MODULE, code=_CODE)
    await crud_tasks.finalize_success(ok)

    r = await client.get(
        f"/internal/tasks/{_MODULE}/{_CODE}/runs", params={"status": "error"}
    )
    assert r.status_code == 200
    assert r.json()["total"] == 0
