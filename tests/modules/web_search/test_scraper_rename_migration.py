"""Переименование скрейпера в данных: ``ccm_003`` + ``wsm_005`` туда и обратно, ``ccm_002``/``wsm_006``.

Код коннектора хранится строкой в четырёх местах — запись доступа, история запросов и страниц,
настройка ``fetch_engine``. Миграции обязаны перевести каждое и не тронуть чужое: тот же код
под другим модулем или другим ключом настройки — не их. Данные кладутся на ревизиях до
переименования, затем цепочка доводится до голов и откатывается назад. Только PostgreSQL
(``heavy``): именно на нём живёт строгая проверка типов, которую SQLite не делает.
"""

from __future__ import annotations

from typing import Any

import pytest
from alembic import command
from sqlalchemy import Connection, inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.apps.app.modules import build_modules
from src.core.config import Config
from src.core.database.migrations import AlembicRunner
from src.core.database.sqlite import WRITE_EXECUTION_OPTIONS, foreign_keys_disabled

pytestmark = pytest.mark.heavy

_BEFORE_RENAME = ("com_005_modules_state", "ccm_002_access_title", "wsm_004_result_page_index")

_SEED = (
    """INSERT INTO core_connectors_access (enabled, connector, is_default, "values", created_at, updated_at)
       VALUES (true, 'web_scrapper', true, '{}', now(), now()),
              (true, 'tavily', true, '{}', now(), now())""",
    """INSERT INTO web_search_query (code, search_engine, fetch_engine, status, query, created_at, updated_at)
       VALUES ('q1', 'tavily', 'web_scrapper', 'done', 'q', now(), now()),
              ('q2', 'tavily', 'firecrawl', 'done', 'q', now(), now())""",
    """INSERT INTO web_search_page (code, status, fetch_engine, url, created_at, updated_at)
       VALUES ('p1', 'done', 'web_scrapper', 'https://a.ru/', now(), now()),
              ('p2', 'done', 'tavily', 'https://b.com/', now(), now()),
              ('p3', 'pending', NULL, 'https://c.com/', now(), now())""",
    """INSERT INTO core_modules_settings (module, key, value, created_at, updated_at)
       VALUES ('web_search', 'fetch_engine', 'web_scrapper', now(), now()),
              ('web_search', 'search_engine', 'web_scrapper', now(), now()),
              ('other', 'fetch_engine', 'web_scrapper', now(), now())""",
)


def _migrate(connection: Connection, verb: str, *targets: str) -> None:
    """``upgrade``/``downgrade`` до названных ревизий тем же путём, каким идёт ``upgrade_head``."""
    connection.execution_options(**WRITE_EXECUTION_OPTIONS)
    with foreign_keys_disabled(connection):
        cfg = AlembicRunner(modules=build_modules())._build_config(connection)
        for target in targets:
            getattr(command, verb)(cfg, target)


async def _run(engine: AsyncEngine, verb: str, *targets: str) -> None:
    async with engine.connect() as conn:
        await conn.run_sync(_migrate, verb, *targets)


async def _rows(engine: AsyncEngine, sql: str) -> list[tuple[Any, ...]]:
    async with engine.connect() as conn:
        return [tuple(row) for row in (await conn.execute(text(sql))).all()]


async def _columns(engine: AsyncEngine, table: str) -> set[str]:
    async with engine.connect() as conn:
        return await conn.run_sync(
            lambda c: {column["name"] for column in inspect(c).get_columns(table)}
        )


async def _stored_codes(engine: AsyncEngine) -> dict[str, list[tuple[Any, ...]]]:
    return {
        "access": await _rows(engine, "SELECT connector FROM core_connectors_access ORDER BY id"),
        "queries": await _rows(engine, "SELECT code, fetch_engine FROM web_search_query ORDER BY code"),
        "pages": await _rows(engine, "SELECT code, fetch_engine FROM web_search_page ORDER BY code"),
        "settings": await _rows(
            engine, "SELECT module, key, value FROM core_modules_settings ORDER BY module, key"
        ),
    }


async def test_the_scraper_code_moves_everywhere_it_is_stored_and_back(config: Config):
    engine = create_async_engine(config.database_url)
    try:
        await _run(engine, "upgrade", *_BEFORE_RENAME)
        async with engine.begin() as conn:
            for statement in _SEED:
                await conn.execute(text(statement))

        await _run(engine, "upgrade", "heads")

        assert await _stored_codes(engine) == {
            "access": [("simple_web_scraper",), ("tavily",)],
            "queries": [("q1", "simple_web_scraper"), ("q2", "firecrawl")],
            "pages": [("p1", "simple_web_scraper"), ("p2", "tavily"), ("p3", None)],
            # Переводится только настройка движка контента web_search — не чужой модуль и не
            # другой ключ с тем же значением
            "settings": [
                ("other", "fetch_engine", "web_scrapper"),
                ("web_search", "fetch_engine", "simple_web_scraper"),
                ("web_search", "search_engine", "web_scrapper"),
            ],
        }
        assert "title" in await _columns(engine, "core_connectors_access")
        assert "fetch_access_id" in await _columns(engine, "web_search_page")

        await _run(engine, "downgrade", "wsm_004_result_page_index", "ccm_001_access")

        assert await _stored_codes(engine) == {
            "access": [("web_scrapper",), ("tavily",)],
            "queries": [("q1", "web_scrapper"), ("q2", "firecrawl")],
            "pages": [("p1", "web_scrapper"), ("p2", "tavily"), ("p3", None)],
            "settings": [
                ("other", "fetch_engine", "web_scrapper"),
                ("web_search", "fetch_engine", "web_scrapper"),
                ("web_search", "search_engine", "web_scrapper"),
            ],
        }
        assert "title" not in await _columns(engine, "core_connectors_access")
        assert "fetch_access_id" not in await _columns(engine, "web_search_page")
    finally:
        await engine.dispose()
