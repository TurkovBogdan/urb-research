"""web_search: дефолтные движки + гейт слотов поиска (троттлинг по in-flight записям)."""

from __future__ import annotations

import pytest

from src.core.config import Config
from src.core.database import close_database, init_database
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.services import searcher
from src.modules.web_search.services.searcher import Searcher


@pytest.mark.pure
def test_default_engines_fall_back_to_tavily_without_settings():
    assert Searcher._default_search_engine() == "tavily"
    assert Searcher._default_fetch_engine() == "tavily"


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    from src.core.database.runtime import Base
    import src.modules.web_search.models  # noqa: F401 — register tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


async def _processing(search_engine: str) -> str:
    row = await query_crud.query_create(
        search_engine=search_engine, fetch_engine="tavily", query="q"
    )
    await query_crud.query_mark_processing(row.code)
    return row.code


@pytest.mark.db
async def test_acquire_slot_returns_immediately_under_limit(db, monkeypatch):
    monkeypatch.setattr(searcher.settings, "max_concurrent_searches", lambda: 2)
    await _processing("tavily")  # 1 активный < 2

    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(searcher.asyncio, "sleep", fake_sleep)
    await searcher._acquire_search_slot("tavily")

    assert slept == []  # слот свободен — без задержки


@pytest.mark.db
async def test_acquire_slot_waits_until_slot_frees(db, monkeypatch):
    monkeypatch.setattr(searcher.settings, "max_concurrent_searches", lambda: 1)
    holder = await _processing("tavily")  # лимит занят

    calls: list[float] = []

    async def free_on_first_wait(seconds: float) -> None:
        calls.append(seconds)
        await query_crud.query_finish(holder)

    monkeypatch.setattr(searcher.asyncio, "sleep", free_on_first_wait)
    await searcher._acquire_search_slot("tavily")

    assert len(calls) == 1  # одна задержка, затем слот освободился


@pytest.mark.db
async def test_acquire_slot_ignores_other_provider_load(db, monkeypatch):
    monkeypatch.setattr(searcher.settings, "max_concurrent_searches", lambda: 1)
    await _processing("firecrawl")  # чужой провайдер занят под завязку

    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(searcher.asyncio, "sleep", fake_sleep)
    await searcher._acquire_search_slot("tavily")  # свой слот свободен

    assert slept == []
