"""web_search: предметные CRUD-тесты по функциям (query / page / result).

PK — голые 22-hex коды: запрос (``random_hash``) и страница (``text_hash`` норм. url). Без ретраев.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import update

from src.core.config import Config
from src.core.database import close_database, init_database, session_scope
from src.core.utils.date import utc_now
from src.core.utils.hashing import text_hash
from src.modules.web_search.constants import (
    FETCH_STATUS_DONE,
    FETCH_STATUS_ERROR,
    FETCH_STATUS_PENDING,
    SEARCH_STATUS_DONE,
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_PENDING,
    SEARCH_STATUS_PROCESSING,
)
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.crud.page import page_code
from src.modules.web_search.models.query import WebSearchQuery


async def _backdate_updated_at(code: str, when) -> None:
    """Состарить ``updated_at`` строки запроса — имитация залипшего/старого ``processing``."""
    async with session_scope() as s:
        await s.execute(
            update(WebSearchQuery).where(WebSearchQuery.code == code).values(updated_at=when)
        )


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


# ── query ────────────────────────────────────────────────────────────────────

@pytest.mark.db
async def test_query_create_get_roundtrip(db):
    row = await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="vector db", params={"depth": "basic"}
    )
    assert len(row.code) == 22
    assert "_" not in row.code
    assert row.status == SEARCH_STATUS_PENDING  # создаётся в pending, работа ещё не началась
    assert row.finished_at is None

    got = await query_crud.query_get(row.code)
    assert got is not None
    assert got.query == "vector db"
    assert got.params == {"depth": "basic"}


@pytest.mark.db
async def test_query_codes_are_unique_per_run(db):
    a = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    b = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    assert a.code != b.code  # случайный код: каждый прогон уникален


@pytest.mark.db
async def test_query_mark_processing(db):
    row = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    processing = await query_crud.query_mark_processing(row.code)
    assert processing is not None
    assert processing.status == SEARCH_STATUS_PROCESSING
    assert processing.finished_at is None


@pytest.mark.db
async def test_query_finish_sets_done_and_timestamp(db):
    row = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    done = await query_crud.query_finish(row.code)
    assert done is not None
    assert done.status == SEARCH_STATUS_DONE  # done даже без результатов (empty убран)
    assert done.finished_at is not None


@pytest.mark.db
async def test_query_mark_error_is_terminal(db):
    row = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    erred = await query_crud.query_mark_error(row.code, error="RuntimeError")
    assert erred is not None
    assert erred.status == SEARCH_STATUS_ERROR
    assert erred.error == "RuntimeError"
    assert erred.finished_at is not None


@pytest.mark.db
async def test_query_get_missing_returns_none(db):
    assert await query_crud.query_get("doesnotexist0000000000") is None


@pytest.mark.db
async def test_query_list_filters(db):
    first = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="vector db")
    await query_crud.query_create(search_engine="firecrawl", fetch_engine="tavily", query="rust async")
    third = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="vector search")

    assert len({s.code for s in await query_crud.query_list()}) == 3

    by_provider = await query_crud.query_list(search_engine="tavily")
    assert {s.code for s in by_provider} == {first.code, third.code}

    by_text = await query_crud.query_list(query="vector")
    assert {s.code for s in by_text} == {first.code, third.code}


@pytest.mark.db
async def test_query_count_matches_filter(db):
    await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="alpha")
    await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="beta")
    await query_crud.query_create(search_engine="firecrawl", fetch_engine="tavily", query="alpha")

    assert await query_crud.query_count() == 3
    assert await query_crud.query_count(search_engine="tavily") == 2
    assert await query_crud.query_count(query="alpha") == 2


@pytest.mark.db
async def test_query_list_paginates(db):
    for i in range(5):
        await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query=f"q{i}")
    first_page = await query_crud.query_list(sort_dir="asc", offset=0, limit=2)
    second_page = await query_crud.query_list(sort_dir="asc", offset=2, limit=2)
    assert len(first_page) == 2
    assert len(second_page) == 2
    assert {s.code for s in first_page}.isdisjoint({s.code for s in second_page})


# ── throttling: подсчёт активных + добивание залипших ────────────────────────

@pytest.mark.db
async def test_query_processing_count_scopes_by_engine_and_freshness(db):
    a = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="a")
    await query_crud.query_mark_processing(a.code)
    b = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="b")
    await query_crud.query_mark_processing(b.code)
    other = await query_crud.query_create(search_engine="firecrawl", fetch_engine="tavily", query="c")
    await query_crud.query_mark_processing(other.code)
    await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="pending")

    fresh_since = utc_now() - timedelta(minutes=1)
    assert await query_crud.query_processing_count("tavily", since=fresh_since) == 2
    assert await query_crud.query_processing_count("firecrawl", since=fresh_since) == 1

    future_since = utc_now() + timedelta(minutes=1)
    assert await query_crud.query_processing_count("tavily", since=future_since) == 0


@pytest.mark.db
async def test_query_expire_stale_reaps_only_old_processing(db):
    stale = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="stale")
    await query_crud.query_mark_processing(stale.code)
    fresh = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="fresh")
    await query_crud.query_mark_processing(fresh.code)
    other = await query_crud.query_create(search_engine="firecrawl", fetch_engine="tavily", query="other")
    await query_crud.query_mark_processing(other.code)
    await _backdate_updated_at(stale.code, utc_now() - timedelta(hours=1))
    await _backdate_updated_at(other.code, utc_now() - timedelta(hours=1))

    reaped = await query_crud.query_expire_stale("tavily", before=utc_now() - timedelta(minutes=30))

    assert reaped == 1  # только старый tavily; чужой движок не трогаем
    stale_row = await query_crud.query_get(stale.code)
    assert stale_row.status == SEARCH_STATUS_ERROR
    assert stale_row.error == "stale"
    assert stale_row.finished_at is not None
    assert (await query_crud.query_get(fresh.code)).status == SEARCH_STATUS_PROCESSING
    assert (await query_crud.query_get(other.code)).status == SEARCH_STATUS_PROCESSING


# ── page ─────────────────────────────────────────────────────────────────────

@pytest.mark.db
async def test_page_upsert_is_idempotent_by_code(db):
    first = await page_crud.page_upsert("https://example.com/p")
    again = await page_crud.page_upsert("https://example.com/p")
    assert first.code == again.code
    assert first.code == page_code("https://example.com/p")
    assert len(first.code) == 22
    assert "_" not in first.code


@pytest.mark.db
async def test_page_upsert_forces_https_and_derives_domain(db):
    page = await page_crud.page_upsert("http://Example.com/a?x=1#frag")
    assert page.url == "https://example.com/a?x=1"  # https + lower host + drop fragment
    assert page.domain == "example.com"
    assert page.code == page_code("https://example.com/a?x=1")


@pytest.mark.db
async def test_page_upsert_sets_title_once_and_keeps_first(db):
    created = await page_crud.page_upsert("https://example.com/t", title="First")
    assert created.title == "First"
    # дедуп по коду: заголовок уже существующей страницы не перетирается
    again = await page_crud.page_upsert("https://example.com/t", title="Second")
    assert again.title == "First"


@pytest.mark.db
async def test_page_set_body_marks_done_with_hash(db):
    page = await page_crud.page_upsert("https://example.com/c")
    updated = await page_crud.page_set_body(page.code, body="# title\nbody")
    assert updated is not None
    assert updated.status == FETCH_STATUS_DONE
    assert updated.body == "# title\nbody"
    assert updated.body_hash == text_hash("# title\nbody")
    assert updated.fetched_at is not None


@pytest.mark.db
async def test_page_set_error_is_terminal(db):
    page = await page_crud.page_upsert("https://example.com/e")
    erred = await page_crud.page_set_error(page.code, error="timeout")
    assert erred is not None
    assert erred.status == FETCH_STATUS_ERROR
    assert erred.error == "timeout"


@pytest.mark.db
async def test_page_list_filters_by_status_domain_and_text(db):
    a = await page_crud.page_upsert("https://alpha.com/x")
    await page_crud.page_upsert("https://beta.com/y")
    fetched = await page_crud.page_upsert("https://alpha.com/z")
    await page_crud.page_set_body(fetched.code, body="body")

    by_domain = await page_crud.page_list(domain="alpha.com")
    assert {p.code for p in by_domain} == {a.code, fetched.code}

    by_status = await page_crud.page_list(status=FETCH_STATUS_DONE)
    assert [p.code for p in by_status] == [fetched.code]

    by_text = await page_crud.page_list(query="beta")
    assert [p.url for p in by_text] == ["https://beta.com/y"]

    assert await page_crud.page_count(domain="alpha.com") == 2
    assert await page_crud.page_count() == 3

    assert (await page_crud.page_upsert("https://beta.com/y")).status == FETCH_STATUS_PENDING


# ── result ───────────────────────────────────────────────────────────────────

@pytest.mark.db
async def test_result_add_dedups_and_orders_by_rank(db):
    query = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    page_a = await page_crud.page_upsert("https://a.com")
    page_b = await page_crud.page_upsert("https://b.com")

    await query_result_crud.result_add(query_code=query.code, page_code=page_b.code, rank=2)
    await query_result_crud.result_add(query_code=query.code, page_code=page_a.code, rank=1, score=0.9)
    # дубль (query_code, page_code) — тихо пропускается
    await query_result_crud.result_add(query_code=query.code, page_code=page_a.code, rank=5)

    rows = await query_result_crud.results_for_query(query.code)
    assert [r.page_code for r in rows] == [page_a.code, page_b.code]  # по rank
    assert rows[0].score == 0.9


@pytest.mark.db
async def test_results_with_page_for_query_joins_page(db):
    query = await query_crud.query_create(search_engine="tavily", fetch_engine="tavily", query="q")
    page_a = await page_crud.page_upsert("https://a.com", title="Alpha")
    await query_result_crud.result_add(
        query_code=query.code, page_code=page_a.code, rank=1, summary="S", meta={"reason": "r"}
    )

    pairs = await query_result_crud.results_with_page_for_query(query.code)
    assert len(pairs) == 1
    result, page = pairs[0]
    assert result.summary == "S"
    assert result.meta == {"reason": "r"}
    assert page.title == "Alpha"  # заголовок — на странице
    assert page.url == "https://a.com"
    assert page.status == FETCH_STATUS_PENDING
