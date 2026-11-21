"""Сервис поиска: прогон «поиск ссылок + получение контента».

Фасад — статический класс ``Searcher``. Публичные ``search_engines()``/``fetch_engines()``
(коды доступных движков по ролям) + два способа запуска:
- ``search(...)`` — **блокирующий**: выполняет прогон целиком и возвращает завершённый запрос
  (для MCP/скриптов/тестов, где нужен результат);
- ``submit(...)`` — **fire-and-forget**: создаёт запрос (``pending``), запускает прогон в фоне
  (``asyncio.create_task``) и **сразу** возвращает ``pending``-строку — вызывающий не ждёт
  (HTTP-эндпойнт создания: клиент видит запрос в очереди, прогресс — поллингом списка).

Обе роли — два движка: движок поиска (``search_engine``) отдаёт ссылки, движок контента
по ним скачивает markdown. Прогон (``_run``): ``pending`` → ``processing`` → движок поиска →
сохранение ссылок → фетч контента страниц (батчами по ``pages_per_request``, параллельно под
семафором ``fetch_concurrency``) → ``done``. Контент качается по политике маршрутов
(``services/fetch_routes.py``): страница из зоны — только своим маршрутом, прочие — основным,
а не полученные им (кроме окончательного «страницы нет») — запасным. Явно названный движок
запроса заменяет политику целиком: один маршрут, без запасного и зон. Очереди/планировщика
нет: сбой движка поиска → запрос ``error`` (исключение не пробрасывается), страница, которую не
получил ни один маршрут, → ``error`` с причиной. Движки — из runtime-настроек; вне
загруженных настроек (скрипт/тест) — дефолты.
Движок без готового доступа в ``core_connectors`` (записи нет, выключена или не заполнена)
ловится до сети: запрос сразу ``error`` (``error="search_engine_disabled"``).

Троттлинг (несколько прогонов бьют по лимитам API): перед началом работы прогон ждёт
свободного слота — не больше ``max_concurrent_searches`` одновременных ``processing`` на
движок (``_acquire_search_slot``, режим задержки). Счётчик — строки в БД (общие для всех
процессов); фоновые ``submit`` самотроттлятся через тот же гейт.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import Any

from src.core.utils.date import utc_now
from src.modules.web_search import settings
from src.modules.web_search.constants import FETCH_STATUS_ERROR, FETCH_STATUS_PENDING
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.providers import SearchEngine
from src.modules.web_search.providers import fetch_engines as fetch_engine_registry
from src.modules.web_search.providers import search_engines as search_engine_registry
from src.modules.web_search.providers.base import FETCH_FINAL_ERRORS, FetchedPage
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.services.fetch_routes import (
    FetchPolicy,
    FetchRoute,
    explicit_policy,
    load_policy,
    split_route_code,
)

# Причина страницы, чей маршрут не может работать: подключения нет, оно выключено или не заполнено.
_ROUTE_DISABLED = "fetch_engine_disabled"

_SLOT_POLL_MIN_SECONDS = 0.5
_SLOT_POLL_MAX_SECONDS = 1.5
_PROCESSING_STALE_TTL = timedelta(minutes=15)

# Потолок одного повтора получения. Большой ремонт режет на куски тот, кто его заказал (браузер
# шлёт их по одному), и кусок обязан укладываться в человеческое ожидание, а не в терпение движка:
# у одной волны батчей ожидание растёт вместе с настройкой параллелизма.
REFETCH_CHUNK_MAX = 50

# Ссылки на живые фоновые прогоны (``submit``): без них ``asyncio`` может собрать task
# сборщиком до завершения. Снимается в done-callback.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


class Searcher:
    """Фасад сервиса поиска: доступные движки + запуск прогона (блокирующий/фоновый)."""

    @staticmethod
    async def search_engines() -> list[str]:
        """Коды движков поиска, чей доступ в ``core_connectors`` готов к работе."""
        return await search_engine_registry.available_codes()

    @staticmethod
    async def fetch_engines() -> list[str]:
        """Коды доступных движков получения контента."""
        return await fetch_engine_registry.available_codes()

    @staticmethod
    async def search(
        query: str,
        *,
        search_engine: str | None = None,
        fetch_engine: str | None = None,
        max_results: int | None = None,
        include_domains: tuple[str, ...] = (),
        exclude_domains: tuple[str, ...] = (),
        time_range: str | None = None,
    ) -> WebSearchQuery:
        """Блокирующий прогон: выполнить целиком и вернуть завершённый запрос."""
        row, request, engine, policy = await Searcher._prepare(
            query,
            search_engine=search_engine,
            fetch_engine=fetch_engine,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        await Searcher._run(row.code, request, engine, policy)
        return await query_crud.query_get(row.code)

    @staticmethod
    async def submit(
        query: str,
        *,
        search_engine: str | None = None,
        fetch_engine: str | None = None,
        max_results: int | None = None,
        include_domains: tuple[str, ...] = (),
        exclude_domains: tuple[str, ...] = (),
        time_range: str | None = None,
    ) -> WebSearchQuery:
        """Fire-and-forget: создать запрос (``pending``), запустить прогон в фоне, вернуть строку сразу."""
        row, request, engine, policy = await Searcher._prepare(
            query,
            search_engine=search_engine,
            fetch_engine=fetch_engine,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        _schedule(Searcher._run(row.code, request, engine, policy))
        return row

    @staticmethod
    async def _prepare(
        query: str,
        *,
        search_engine: str | None,
        fetch_engine: str | None,
        max_results: int | None,
        include_domains: tuple[str, ...],
        exclude_domains: tuple[str, ...],
        time_range: str | None,
    ) -> tuple[WebSearchQuery, SearchRequest, SearchEngine, FetchPolicy]:
        """Резолвит движки (падает ``KeyError`` на неизвестном коде ДО создания строки) и
        создаёт запрос в ``pending`` со снимком движка поиска и основного маршрута контента."""
        request = SearchRequest(
            query=query,
            max_results=max_results if max_results is not None else settings.default_pages(),
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        engine = search_engine_registry.get(search_engine or Searcher._default_search_engine())
        policy = await Searcher._fetch_policy(fetch_engine)
        row = await query_crud.query_create(
            search_engine=engine.code,
            fetch_engine=fetch_engine or Searcher._default_fetch_engine(),
            query=request.query,
            params=request.to_params(),
        )
        return row, request, engine, policy

    @staticmethod
    async def _run(
        code: str, request: SearchRequest, engine: SearchEngine, policy: FetchPolicy
    ) -> None:
        """Прогон запроса ``code``: гейт слота → ``processing`` → поиск → сохранение → фетч → ``done``.

        Сбой движка поиска → запрос ``error`` (без исключения); страница, которую не получил
        ни один маршрут, → ``error``.
        """
        if not await engine.available():
            await query_crud.query_mark_error(code, error="search_engine_disabled")
            return
        await _acquire_search_slot(engine.code)
        await query_crud.query_mark_processing(code)

        try:
            results = await engine.search(request)
        except Exception as exc:  # noqa: BLE001 — сбой движка → терминальный error (без повторов)
            await query_crud.query_mark_error(code, error=type(exc).__name__)
            return

        pending = await _store_results(code, results)
        await _fetch_pages(policy, pending)
        await query_crud.query_finish(code)

    @staticmethod
    async def refetch(page_codes: list[str], *, fetch_engine: str | None = None) -> None:
        """Повторно получить контент уже известных страниц (без поиска).

        Единственный вход для «страница не скачалась — попробуем ещё раз»: фетч сам не
        повторяется, а поисковый движок тут не участвует (слот-гейт не нужен, лимиты у
        движка контента свои). Страницы идут по той же политике маршрутов, что и в поиске.
        Ни одного готового маршрута — ошибка до сети, а не сотня страниц в ``error``;
        недоступный по сети — обычный исход, страница получает ``error``.
        """
        policy = await Searcher._fetch_policy(fetch_engine)
        if not policy.any_ready:
            raise RuntimeError(_ROUTE_DISABLED)
        await _fetch_pages(policy, await page_crud.pages_by_codes(page_codes))

    @staticmethod
    def refetch_chunk_size(*, fetch_engine: str | None = None) -> int:
        """Сколько страниц просить за один ``refetch``, чтобы основной маршрут сделал ровно
        одну волну батчей."""
        engine_code, _ = split_route_code(fetch_engine or Searcher._default_fetch_engine())
        per_request = fetch_engine_registry.get(engine_code).pages_per_request
        return min(per_request * settings.fetch_concurrency(), REFETCH_CHUNK_MAX)

    @staticmethod
    async def _fetch_policy(fetch_engine: str | None) -> FetchPolicy:
        """Явный движок запроса — один маршрут; без него — политика из настроек."""
        if fetch_engine:
            return await explicit_policy(fetch_engine)
        return await load_policy(
            Searcher._default_fetch_engine(),
            settings.fetch_engine_fallback(),
            settings.fetch_engine_zones(),
            settings.fetch_engine_fallback_zones(),
        )

    @staticmethod
    def _default_search_engine() -> str:
        """Дефолтный движок поиска (настройка), когда в запуске не передан явный."""
        return settings.search_engine()

    @staticmethod
    def _default_fetch_engine() -> str:
        """Дефолтный движок контента (настройка), когда в запуске не передан явный."""
        return settings.fetch_engine()


def _schedule(coro: Any) -> None:
    """Запустить корутину фоном (``submit``), удержав ссылку до завершения."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def _acquire_search_slot(search_engine: str) -> None:
    """Дождаться свободного слота под поиск этим движком — режим задержки, не ошибки.

    Слот = строка запроса в ``processing``. Ждём, пока свежих ``processing`` по движку меньше
    лимита (``max_concurrent_searches``), опрашивая с джиттером (чтобы стадо ожидающих не
    просыпалось разом). Перед подсчётом добиваем залипшие ``processing`` (краш процесса) →
    ``error``, иначе они держали бы слот вечно (reaper inline — у модуля нет планировщика; TTL
    даёт и гарантию прогресса: ждущий разблокируется максимум через ``_PROCESSING_STALE_TTL``).
    Лимит мягкий: между проверкой и захватом слота (``query_mark_processing``) возможен
    кратковременный перебор — держим лимит с запасом ниже реального лимита API.
    """
    limit = settings.max_concurrent_searches()
    while True:
        cutoff = utc_now() - _PROCESSING_STALE_TTL
        await query_crud.query_expire_stale(search_engine, before=cutoff)
        active = await query_crud.query_processing_count(search_engine, since=cutoff)
        if active < limit:
            return
        await asyncio.sleep(random.uniform(_SLOT_POLL_MIN_SECONDS, _SLOT_POLL_MAX_SECONDS))


async def _store_results(
    query_code: str, results: Sequence[Mapping[str, Any]]
) -> list[WebSearchPage]:
    """Привязать ссылки выдачи к запросу (page → result); вернуть страницы под до-фетч.

    Под каждый url создаётся (или переиспользуется по дедупу) ``web_search_page`` в
    ``pending``. Возвращает страницы **без контента** — новые ``pending`` и осевшие в
    ``error`` от прошлых прогонов: дедуп по url вечен, поэтому иначе однажды упавшая страница
    не скачалась бы уже никогда. Уже ``done`` — переиспользуются и в список не попадают.
    Статус запроса тут не трогается. Контент движок поиска не отдаёт — это отдельная роль
    (``_fetch_pages``).
    """
    unfetched: dict[str, WebSearchPage] = {}
    for result in results:
        page = await page_crud.page_upsert(result["url"], title=result.get("title"))
        if page.status in (FETCH_STATUS_PENDING, FETCH_STATUS_ERROR):
            unfetched[page.code] = page
        await query_result_crud.result_add(
            query_code=query_code,
            page_code=page.code,
            rank=result.get("rank"),
            score=result.get("score"),
            summary=result.get("summary"),
            meta=result.get("meta"),
        )
    return list(unfetched.values())


async def _fetch_pages(policy: FetchPolicy, pages: list[WebSearchPage]) -> None:
    """Дотянуть контент страниц по политике маршрутов.

    Первый проход — каждая страница своим маршрутом (зона или основной); второй — запасной
    для тех, кого основной не получил и кому запасной разрешён. Семафор ``fetch_concurrency``
    один на оба прохода и на все маршруты.
    """
    if not pages:
        return
    semaphore = asyncio.Semaphore(settings.fetch_concurrency())
    by_route: dict[FetchRoute | None, list[WebSearchPage]] = {}
    may_fall_back: set[str] = set()
    for page in pages:
        route, fallback_allowed = policy.route_for(page.domain)
        by_route.setdefault(route, []).append(page)
        if fallback_allowed:
            may_fall_back.add(page.code)

    first_pass = await asyncio.gather(
        *(
            _fetch_route(route, group, semaphore, may_fall_back=may_fall_back)
            for route, group in by_route.items()
        )
    )
    left_over = [page for group in first_pass for page in group]
    if left_over:
        await _fetch_route(policy.fallback, left_over, semaphore, may_fall_back=set())


async def _fetch_route(
    route: FetchRoute | None,
    pages: list[WebSearchPage],
    semaphore: asyncio.Semaphore,
    *,
    may_fall_back: set[str],
) -> list[WebSearchPage]:
    """Получить страницы одним маршрутом; вернуть те, что остались для запасного.

    Страница, которую маршрут не получил, остаётся без итога, только если ей разрешён
    запасной и причина не окончательная (``FETCH_FINAL_ERRORS``); прочие получают ``error``
    сразу. Неготовый маршрут в сеть не ходит — его страницы не получены по ``_ROUTE_DISABLED``.
    """
    left_over: list[WebSearchPage] = []

    async def settle(page: WebSearchPage, result: FetchedPage) -> None:
        if result.content:
            await page_crud.page_set_body(page.code, body=result.content)
        elif page.code in may_fall_back and result.error not in FETCH_FINAL_ERRORS:
            left_over.append(page)
        else:
            await page_crud.page_set_error(page.code, error=result.error or "empty")

    if route is None or not route.ready:
        for page in pages:
            await settle(page, FetchedPage(error=_ROUTE_DISABLED))
        return left_over

    per_request = route.engine.pages_per_request
    batches = [pages[i:i + per_request] for i in range(0, len(pages), per_request)]

    async def run(batch: list[WebSearchPage]) -> None:
        async with semaphore:
            await page_crud.pages_mark_processing(
                [p.code for p in batch],
                fetch_engine=route.engine.code,
                fetch_access_id=route.access_id,
            )
            try:
                results = await route.engine.fetch_pages(
                    [p.url for p in batch], access=route.access_id
                )
            except Exception as exc:  # noqa: BLE001 — сбой батча — причина для каждой его страницы
                results = {p.url: FetchedPage(error=type(exc).__name__) for p in batch}
            for page in batch:
                await settle(page, results.get(page.url, FetchedPage(error="empty")))

    await asyncio.gather(*(run(batch) for batch in batches))
    return left_over


__all__ = ["REFETCH_CHUNK_MAX", "Searcher"]
