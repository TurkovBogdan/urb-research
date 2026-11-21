"""web_search: приём строк переноса — код переименованного движка контента приводится к нынешнему.

Архив мог уехать из установки, где скрейпер ещё звался ``web_scrapper``: его страницы и
прогоны должны лечь под кодом, который знает реестр движков этой базы.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select

from src.core.config import Config
from src.core.database import close_database, init_database, session_scope, write_scope
from src.core.database.runtime import Base
from src.core.utils.date import utc_now
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.services import transfer

pytestmark = pytest.mark.db


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


def _page(code: str, fetch_engine: str | None) -> dict[str, Any]:
    now = utc_now()
    return {
        "code": code,
        "url": f"https://{code}.ru/",
        "status": "done",
        "fetch_engine": fetch_engine,
        "created_at": now,
        "updated_at": now,
    }


def _search(code: str, fetch_engine: str) -> dict[str, Any]:
    now = utc_now()
    return {
        "code": code,
        "search_engine": "tavily",
        "fetch_engine": fetch_engine,
        "status": "done",
        "query": "запрос",
        "created_at": now,
        "updated_at": now,
    }


async def _stored_engine(model: type[WebSearchPage] | type[WebSearchQuery], code: str) -> str | None:
    async with session_scope() as s:
        return (await s.execute(select(model.fetch_engine).where(model.code == code))).scalar_one()


async def test_pages_from_an_old_archive_land_under_the_current_engine_code(db):
    await transfer.pages_insert(
        [_page("p1", "web_scrapper"), _page("p2", "tavily"), _page("p3", None)]
    )

    assert await _stored_engine(WebSearchPage, "p1") == "simple_web_scraper"
    assert await _stored_engine(WebSearchPage, "p2") == "tavily"
    assert await _stored_engine(WebSearchPage, "p3") is None


async def test_an_imported_page_forgets_the_connection_of_its_home_install(db):
    # id подключения принадлежит установке-источнику: здесь под ним может лежать чужое
    await transfer.pages_insert([{**_page("p1", "simple_web_scraper"), "fetch_access_id": 5}])
    await transfer.pages_insert([{**_page("p2", None), "fetch_access_id": None}])
    async with write_scope() as s:
        await s.execute(
            WebSearchPage.__table__.update()
            .where(WebSearchPage.code == "p2")
            .values(fetch_access_id=9)
        )
    await transfer.page_fill_material(
        "p2",
        body="# B",
        body_hash=None,
        status="done",
        fetch_engine="simple_web_scraper",
        fetched_at=utc_now(),
        error=None,
    )

    async with session_scope() as s:
        stored = dict(
            (await s.execute(select(WebSearchPage.code, WebSearchPage.fetch_access_id))).all()
        )
    assert stored == {"p1": None, "p2": None}


async def test_merged_page_material_takes_the_current_engine_code(db):
    await transfer.pages_insert([_page("p1", None)])

    await transfer.page_fill_material(
        "p1",
        body="# A",
        body_hash=None,
        status="done",
        fetch_engine="web_scrapper",
        fetched_at=utc_now(),
        error=None,
    )

    assert await _stored_engine(WebSearchPage, "p1") == "simple_web_scraper"


async def test_searches_from_an_old_archive_land_under_the_current_engine_code(db):
    await transfer.searches_insert([_search("s1", "web_scrapper"), _search("s2", "tavily")])
    await transfer.search_replace("s2", {"fetch_engine": "web_scrapper"})

    assert await _stored_engine(WebSearchQuery, "s1") == "simple_web_scraper"
    assert await _stored_engine(WebSearchQuery, "s2") == "simple_web_scraper"


async def test_an_imported_search_keeps_its_engine_but_not_the_connection_of_its_home(db):
    # Прогон хранит код маршрута; id подключения в нём — чужой установки
    await transfer.searches_insert(
        [_search("s1", "simple_web_scraper:7"), _search("s2", "web_scrapper:3")]
    )
    await transfer.searches_insert([_search("s3", "tavily")])
    await transfer.search_replace("s3", {"fetch_engine": "firecrawl:12"})

    assert [await _stored_engine(WebSearchQuery, code) for code in ("s1", "s2", "s3")] == [
        "simple_web_scraper",
        "simple_web_scraper",
        "firecrawl",
    ]
