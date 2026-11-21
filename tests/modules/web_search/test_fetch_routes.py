"""web_search: маршруты получения контента — коды, зоны, политика и запасной проход.

Маршрут — движок вместе с подключением; политика — основной маршрут, запасной и их зоны.
Чистая часть (коды, зоны, выбор маршрута) проверяется без базы; варианты для настроек и
разрешение подключений — на записях доступа; сам проход — ``Searcher.refetch`` на движках-
заглушках, которые записывают, какие url им достались.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.modules.core_connectors import service as connectors_service
from src.modules.web_search import settings
from src.modules.web_search.constants import FETCH_STATUS_DONE, FETCH_STATUS_ERROR
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud.page import page_code
from src.modules.web_search.providers import registry
from src.modules.web_search.providers.base import FetchedPage, FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.services.fetch_routes import (
    FetchPolicy,
    FetchRoute,
    fallback_route_options,
    load_policy,
    matching_zone,
    normalize_domain,
    normalized_zones,
    resolve_route,
    route_options,
    split_route_code,
)
from src.modules.web_search.services.searcher import Searcher


class _FetchStub(FetchEngine):
    """Движок контента без сети: отдаёт заданные итоги и помнит, какие url получил."""

    def __init__(
        self,
        code: str,
        *,
        pages: dict[str, FetchedPage] | None = None,
        ready: bool = True,
        per_request: int = 10,
        raises: Exception | None = None,
    ):
        self.code = code
        self.pages_per_request = per_request
        self.ready = ready
        self.pages = pages or {}
        self.raises = raises
        self.batches: list[list[str]] = []
        self.accesses: list[int | None] = []

    @property
    def seen(self) -> list[str]:
        return [url for batch in self.batches for url in batch]

    async def available(self, access: int | None = None) -> bool:
        return self.ready

    async def fetch_pages(
        self, urls: list[str], *, access: int | None = None
    ) -> dict[str, FetchedPage]:
        self.batches.append(list(urls))
        self.accesses.append(access)
        if self.raises is not None:
            raise self.raises
        return {url: self.pages.get(url, FetchedPage(error="empty")) for url in urls}


def _route(code: str) -> FetchRoute:
    return FetchRoute(code=code, engine=_FetchStub(code), access_id=None, ready=True)


# ── коды и зоны ──────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_route_code_names_an_engine_and_optionally_its_connection():
    assert split_route_code("tavily") == ("tavily", None)
    assert split_route_code("simple_web_scraper:6") == ("simple_web_scraper", 6)
    with pytest.raises(KeyError):
        split_route_code("simple_web_scraper:vpn")


@pytest.mark.pure
def test_zones_are_compared_in_the_form_domains_are_stored():
    # Домены страниц лежат в punycode: зона «.рф» обязана совпасть с «xn--p1ai»
    assert normalize_domain(".рф") == "xn--p1ai"
    assert normalize_domain("*.Example.RU") == "example.ru"
    assert normalize_domain("пример.рф") == "xn--e1afmkfd.xn--p1ai"
    assert normalize_domain("  ") is None


@pytest.mark.pure
def test_a_zone_covers_the_domain_and_its_subdomains_only():
    zones = ("ru", "example.ru")

    assert matching_zone("example.ru", zones) == "example.ru"  # самая узкая
    assert matching_zone("news.example.ru", zones) == "example.ru"
    assert matching_zone("site.ru", zones) == "ru"
    assert matching_zone("nonru.com", zones) is None  # хвост метки — не зона
    assert matching_zone(None, zones) is None


# ── выбор маршрута ───────────────────────────────────────────────────────────


@pytest.mark.pure
def test_a_page_outside_zones_goes_to_the_primary_with_a_fallback_behind_it():
    primary, fallback = _route("main"), _route("spare")

    assert FetchPolicy(primary, fallback).route_for("site.com") == (primary, True)
    assert FetchPolicy(primary).route_for("site.com") == (primary, False)


@pytest.mark.pure
def test_a_fallback_zone_sends_the_page_straight_to_the_fallback():
    primary, fallback = _route("main"), _route("spare")
    policy = FetchPolicy(primary, fallback, fallback_zones=("ru", "xn--p1ai"))

    assert policy.route_for("site.ru") == (fallback, False)
    assert policy.route_for("xn--80a.xn--p1ai") == (fallback, False)  # .рф из настроек
    assert policy.route_for("site.com") == (primary, True)


@pytest.mark.pure
def test_the_narrower_zone_wins_when_both_sides_claim_a_domain():
    primary, fallback = _route("main"), _route("spare")
    policy = FetchPolicy(
        primary, fallback, primary_zones=("example.ru",), fallback_zones=("ru",)
    )

    assert policy.route_for("news.example.ru") == (primary, False)  # основной и без запасного
    assert policy.route_for("other.ru") == (fallback, False)


@pytest.mark.pure
def test_fallback_zones_mean_nothing_without_a_fallback():
    primary = _route("main")

    assert FetchPolicy(primary, fallback_zones=("ru",)).route_for("site.ru") == (primary, False)


@pytest.mark.pure
def test_an_unready_fallback_takes_no_overflow_but_keeps_its_zones():
    primary = _route("main")
    fallback = FetchRoute(code="spare", engine=_FetchStub("spare"), access_id=None, ready=False)
    policy = FetchPolicy(primary, fallback, fallback_zones=("ru",))

    assert policy.route_for("site.com") == (primary, False)
    assert policy.route_for("site.ru") == (fallback, False)  # зона — только своим маршрутом


@pytest.mark.pure
def test_the_same_zone_on_both_sides_goes_to_the_primary():
    primary, fallback = _route("main"), _route("spare")
    policy = FetchPolicy(primary, fallback, primary_zones=("ru",), fallback_zones=("ru",))

    assert policy.route_for("site.ru") == (primary, False)


@pytest.mark.pure
def test_a_page_without_a_domain_takes_the_ordinary_path():
    primary, fallback = _route("main"), _route("spare")
    policy = FetchPolicy(primary, fallback, fallback_zones=("ru",))

    assert policy.route_for(None) == (primary, True)


@pytest.mark.pure
def test_a_zone_typed_in_cyrillic_meets_the_domain_however_it_is_stored():
    primary, fallback = _route("main"), _route("spare")
    policy = FetchPolicy(primary, fallback, fallback_zones=normalized_zones([".РФ"]))

    # В базе домены лежат в punycode — так их сохраняет выдача поиска
    assert policy.route_for("xn--e1afmkfd.xn--p1ai") == (fallback, False)
    # Но адрес мог прийти и с кириллическим хостом — сравнение всё равно в punycode
    assert policy.route_for("пример.рф") == (fallback, False)


@pytest.mark.pure
def test_blank_and_broken_zones_are_dropped_not_fatal():
    zones = normalized_zones(["", "  ", ".ru", "a..b", "x" * 64 + ".com", "*.example.com"])

    assert zones == ("ru", "example.com")  # метка длиннее 63 символов — не домен


@pytest.mark.pure
def test_a_route_code_with_an_empty_connection_is_not_a_route():
    with pytest.raises(KeyError):
        split_route_code("simple_web_scraper:")


# ── варианты для настроек и подключения ──────────────────────────────────────


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    import src.modules.core_connectors.access.model  # noqa: F401 — register tables
    import src.modules.web_search.models  # noqa: F401 — register tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_each_scraper_connection_becomes_its_own_option(db):
    direct = await connectors_service.create_access(
        connector="simple_web_scraper", title="Напрямую", values={}
    )
    untitled = await connectors_service.create_access(connector="simple_web_scraper", values={})

    options = dict(await route_options())

    assert options["tavily"] == "Tavily"  # одно подключение или ни одного — выбирать нечего
    # Первое стоит за кодом движка — его хранит настройка по умолчанию — и подписано своим именем
    assert options["simple_web_scraper"] == "SimpleWebScraper · Напрямую"
    assert f"simple_web_scraper:{direct.id}" not in options
    assert options[f"simple_web_scraper:{untitled.id}"] == "SimpleWebScraper · Подключение 2"
    assert not any("по умолчанию" in label for label in options.values())


@pytest.mark.db
async def test_a_route_goes_through_the_named_connection_of_its_own_connector_only(db):
    direct = await connectors_service.create_access(connector="simple_web_scraper", values={})
    vpn = await connectors_service.create_access(
        connector="simple_web_scraper", values={"base_url": "http://127.0.0.1:19021"}
    )
    foreign = await connectors_service.create_access(
        connector="tavily", values={"api_key": "k"}
    )

    by_default = await resolve_route("simple_web_scraper")
    named = await resolve_route(f"simple_web_scraper:{vpn.id}")
    other_vendor = await resolve_route(f"simple_web_scraper:{foreign.id}")

    assert (by_default.access_id, by_default.ready) == (direct.id, True)
    assert (named.access_id, named.ready) == (vpn.id, True)
    # Ключ одного вендора не уходит другому: чужая запись делает маршрут неготовым
    assert (other_vendor.access_id, other_vendor.ready) == (None, False)


@pytest.mark.db
async def test_a_single_connection_is_offered_only_as_its_engine(db):
    await connectors_service.create_access(
        connector="simple_web_scraper", title="Напрямую", values={}
    )

    codes = [code for code, _ in await route_options()]
    fallback = await fallback_route_options()

    assert "simple_web_scraper" in codes
    assert not any(code.startswith("simple_web_scraper:") for code in codes)
    assert fallback[0] == ("", "Нет")  # запасной можно не выбирать — вариант первым
    assert [code for code, _ in fallback[1:]] == codes


@pytest.mark.db
async def test_a_disabled_or_missing_connection_makes_its_route_not_ready(db):
    await connectors_service.create_access(connector="simple_web_scraper", values={})
    vpn = await connectors_service.create_access(connector="simple_web_scraper", values={})
    await connectors_service.update_access(vpn.id, enabled=False)

    disabled = await resolve_route(f"simple_web_scraper:{vpn.id}")
    nothing = await resolve_route("firecrawl")  # у коннектора нет ни одного подключения

    assert (disabled.access_id, disabled.ready) == (vpn.id, False)
    assert (nothing.access_id, nothing.ready) == (None, False)


@pytest.mark.db
async def test_a_policy_survives_a_setting_that_names_no_engine(db):
    # Например, код, переименованный после того, как его записали в настройку
    policy = await load_policy("web_scrapper", "", [], [".РФ", ""])

    assert policy.primary is None
    assert policy.fallback is None
    assert policy.primary_zones == ()
    assert policy.any_ready is False


@pytest.mark.db
async def test_a_deleted_connection_leaves_its_route_not_ready(db):
    await connectors_service.create_access(connector="simple_web_scraper", values={})
    vpn = await connectors_service.create_access(connector="simple_web_scraper", values={})
    await connectors_service.delete_access(vpn.id)

    route = await resolve_route(f"simple_web_scraper:{vpn.id}")

    assert route.ready is False  # ошибка видна, а не тихий переезд на соседнее подключение


# ── проход по политике ───────────────────────────────────────────────────────


@pytest.fixture
def routes(monkeypatch):
    """Поставить два движка-заглушки и политику: ``routes(main, spare, zones…)``."""

    def _install(
        main: _FetchStub,
        spare: _FetchStub | None = None,
        *,
        main_zones: tuple[str, ...] = (),
        spare_zones: tuple[str, ...] = (),
    ) -> None:
        monkeypatch.setitem(registry.fetch_engines._engines, main.code, main)
        if spare is not None:
            monkeypatch.setitem(registry.fetch_engines._engines, spare.code, spare)
        monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: main.code)
        monkeypatch.setattr(settings, "fetch_engine_fallback", lambda: spare.code if spare else "")
        monkeypatch.setattr(settings, "fetch_engine_zones", lambda: list(main_zones))
        monkeypatch.setattr(settings, "fetch_engine_fallback_zones", lambda: list(spare_zones))

    return _install


async def _pages(*urls: str) -> dict[str, Any]:
    return {url: await page_crud.page_upsert(url) for url in urls}


async def _refetched(pages: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    await Searcher.refetch([page.code for page in pages.values()], **kwargs)
    return {url: await page_crud.page_get_by_code(page.code) for url, page in pages.items()}


@pytest.mark.db
async def test_a_page_the_primary_could_not_get_goes_to_the_fallback(db, routes):
    url = "https://wall.com/a"
    main = _FetchStub("main", pages={url: FetchedPage(error="access_denied")})
    spare = _FetchStub("spare", pages={url: FetchedPage(content="# A")})
    routes(main, spare)

    page = (await _refetched(await _pages(url)))[url]

    assert (page.status, page.body, page.fetch_engine) == (FETCH_STATUS_DONE, "# A", "spare")
    assert main.seen == [url] and spare.seen == [url]


@pytest.mark.db
async def test_a_missing_page_does_not_go_to_the_fallback(db, routes):
    url = "https://gone.com/a"
    main = _FetchStub("main", pages={url: FetchedPage(error="not_found")})
    spare = _FetchStub("spare", pages={url: FetchedPage(content="# never")})
    routes(main, spare)

    page = (await _refetched(await _pages(url)))[url]

    assert (page.status, page.error) == (FETCH_STATUS_ERROR, "not_found")
    assert spare.seen == []  # страницы нет — другой путь этого не изменит


@pytest.mark.db
async def test_a_fallback_zone_page_skips_the_primary_and_gets_no_second_try(db, routes):
    ru, com = "https://site.ru/a", "https://site.com/a"
    main = _FetchStub("main", pages={com: FetchedPage(content="# com")})
    spare = _FetchStub("spare", pages={ru: FetchedPage(error="timeout")})
    routes(main, spare, spare_zones=(".ru",))

    pages = await _refetched(await _pages(ru, com))

    assert main.seen == [com]  # .ru основной не видит вовсе
    assert spare.seen == [ru]
    assert (pages[ru].status, pages[ru].error) == (FETCH_STATUS_ERROR, "timeout")
    assert pages[com].status == FETCH_STATUS_DONE


@pytest.mark.db
async def test_a_primary_zone_page_is_not_handed_to_the_fallback(db, routes):
    url = "https://example.org/a"
    main = _FetchStub("main", pages={url: FetchedPage(error="upstream_down")})
    spare = _FetchStub("spare", pages={url: FetchedPage(content="# spare")})
    routes(main, spare, main_zones=(".org",))

    page = (await _refetched(await _pages(url)))[url]

    assert (page.status, page.error) == (FETCH_STATUS_ERROR, "upstream_down")
    assert spare.seen == []


@pytest.mark.db
async def test_pages_of_an_unavailable_primary_go_to_the_fallback(db, routes):
    url = "https://site.com/a"
    main = _FetchStub("main", ready=False)
    spare = _FetchStub("spare", pages={url: FetchedPage(content="# spare")})
    routes(main, spare)

    page = (await _refetched(await _pages(url)))[url]

    assert (page.status, page.fetch_engine) == (FETCH_STATUS_DONE, "spare")
    assert main.seen == []  # неготовый маршрут в сеть не ходит


@pytest.mark.db
async def test_a_page_keeps_the_reason_of_the_primary_when_the_fallback_is_unavailable(
    db, routes
):
    url = "https://wall.com/a"
    main = _FetchStub("main", pages={url: FetchedPage(error="access_denied")})
    spare = _FetchStub("spare", ready=False)
    routes(main, spare)

    page = (await _refetched(await _pages(url)))[url]

    # Запасной не ходил — причина остаётся за тем, кто ходил
    assert (page.status, page.error, page.fetch_engine) == (
        FETCH_STATUS_ERROR,
        "access_denied",
        "main",
    )
    assert spare.seen == []


@pytest.mark.db
async def test_refetch_refuses_when_no_route_is_ready(db, routes):
    routes(_FetchStub("main", ready=False), _FetchStub("spare", ready=False))

    with pytest.raises(RuntimeError, match="fetch_engine_disabled"):
        await _refetched(await _pages("https://site.com/a"))


@pytest.mark.db
async def test_an_explicit_engine_replaces_the_policy_without_a_fallback(db, routes):
    url = "https://wall.com/a"
    main = _FetchStub("main", pages={url: FetchedPage(error="access_denied")})
    spare = _FetchStub("spare", pages={url: FetchedPage(content="# A")})
    routes(main, spare)

    page = (await _refetched(await _pages(url), fetch_engine="main"))[url]

    assert (page.status, page.error) == (FETCH_STATUS_ERROR, "access_denied")
    assert spare.seen == []


@pytest.mark.db
async def test_only_the_failed_pages_of_a_batch_go_to_the_fallback(db, routes):
    urls = [f"https://site{i}.com/" for i in range(5)]
    main = _FetchStub(
        "main",
        per_request=2,
        pages={
            urls[0]: FetchedPage(content="# 0"),
            urls[1]: FetchedPage(error="timeout"),
            urls[2]: FetchedPage(content="# 2"),
            urls[3]: FetchedPage(error="access_denied"),
            urls[4]: FetchedPage(content="# 4"),
        },
    )
    spare = _FetchStub("spare", pages={urls[1]: FetchedPage(content="# 1")})
    routes(main, spare)

    pages = await _refetched(await _pages(*urls))

    assert sorted(len(batch) for batch in main.batches) == [1, 2, 2]  # батчи основного — по 2
    assert len(spare.batches) == 1 and sorted(spare.seen) == [urls[1], urls[3]]
    assert [(pages[u].status, pages[u].fetch_engine) for u in (urls[0], urls[2], urls[4])] == [
        (FETCH_STATUS_DONE, "main")
    ] * 3
    assert (pages[urls[1]].status, pages[urls[1]].body) == (FETCH_STATUS_DONE, "# 1")
    # Не получил и запасной — причина его, а не основного
    assert (pages[urls[3]].status, pages[urls[3]].error) == (FETCH_STATUS_ERROR, "empty")


@pytest.mark.db
async def test_a_failed_batch_goes_to_the_fallback_and_its_failure_is_named(db, routes):
    url = "https://site.com/a"
    main = _FetchStub("main", raises=ConnectionError("daemon down"))
    spare = _FetchStub("spare", raises=TimeoutError("spare down"))
    routes(main, spare)

    page = (await _refetched(await _pages(url)))[url]

    assert spare.seen == [url]  # упавший батч основного — повод отдать страницы запасному
    assert (page.status, page.error, page.fetch_engine) == (
        FETCH_STATUS_ERROR,
        "TimeoutError",
        "spare",
    )


@pytest.mark.db
async def test_a_page_remembers_the_connection_that_fetched_it(db, monkeypatch):
    direct = await connectors_service.create_access(connector="simple_web_scraper", values={})
    vpn = await connectors_service.create_access(connector="simple_web_scraper", values={})
    ru, com = "https://site.ru/a", "https://site.com/a"
    engine = _FetchStub(
        "simple_web_scraper",
        pages={ru: FetchedPage(content="# ru"), com: FetchedPage(content="# com")},
    )
    monkeypatch.setitem(registry.fetch_engines._engines, engine.code, engine)
    monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: "simple_web_scraper")
    monkeypatch.setattr(settings, "fetch_engine_fallback", lambda: f"simple_web_scraper:{vpn.id}")
    monkeypatch.setattr(settings, "fetch_engine_zones", lambda: [])
    monkeypatch.setattr(settings, "fetch_engine_fallback_zones", lambda: [".ru"])

    pages = await _refetched(await _pages(ru, com))

    assert (pages[com].fetch_access_id, pages[ru].fetch_access_id) == (direct.id, vpn.id)
    assert sorted(engine.accesses) == sorted([direct.id, vpn.id])  # движок шёл через подключение маршрута


class _FinderStub(SearchEngine):
    code = "finder"

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results

    async def available(self, access: int | None = None) -> bool:
        return True

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        return self.results


@pytest.mark.db
async def test_a_search_fetches_its_links_by_the_same_policy(db, routes, monkeypatch):
    ru, com = "https://site.ru/a", "https://site.com/a"
    main = _FetchStub("main", pages={com: FetchedPage(content="# com")})
    spare = _FetchStub("spare", pages={ru: FetchedPage(content="# ru")})
    routes(main, spare, spare_zones=(".ru",))
    finder = _FinderStub([{"url": ru, "rank": 1}, {"url": com, "rank": 2}])
    monkeypatch.setitem(registry.search_engines._engines, finder.code, finder)
    monkeypatch.setattr(Searcher, "_default_search_engine", lambda: finder.code)

    query = await Searcher.search("q")

    assert query.fetch_engine == "main"  # снимок основного маршрута
    assert (main.seen, spare.seen) == ([com], [ru])
    stored = [await page_crud.page_get_by_code(page_code(url)) for url in (ru, com)]
    assert [page.status for page in stored] == [FETCH_STATUS_DONE, FETCH_STATUS_DONE]


@pytest.mark.pure
def test_the_refetch_chunk_follows_the_engine_of_a_route_code(monkeypatch):
    monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: "simple_web_scraper:7")
    monkeypatch.setattr(settings, "fetch_concurrency", lambda: 3)

    assert Searcher.refetch_chunk_size() == 30  # 10 страниц на запрос скрейпера × 3
