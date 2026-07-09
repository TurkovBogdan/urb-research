"""Сервис поиска: прогон «поиск ссылок + получение контента».

Фасад — статический класс ``Searcher``. Публичные ``search_engines()``/``fetch_engines()``
(коды доступных движков по ролям) + два способа запуска:
- ``search(...)`` — **блокирующий**: выполняет прогон целиком и возвращает завершённый запрос
  (для MCP/скриптов/тестов, где нужен результат);
- ``submit(...)`` — **fire-and-forget**: создаёт запрос (``pending``), запускает прогон в фоне
  (``asyncio.create_task``) и **сразу** возвращает ``pending``-строку — вызывающий не ждёт
  (HTTP-эндпойнт создания: клиент видит запрос в очереди, прогресс — поллингом списка).

Обе роли — два движка: движок поиска (``search_engine``) отдаёт ссылки, движок контента
(``fetch_engine``) по ним скачивает markdown. Прогон (``_run``): ``pending`` → ``processing``
→ движок поиска → сохранение ссылок → фетч контента страниц (батчами по ``pages_per_request``,
параллельно под семафором ``fetch_concurrency``) → ``done``. Очереди/планировщика/ретраев нет:
сбой движка → запрос ``error`` (исключение не пробрасывается), сбой страницы → эта страница
``error``. Движки — из runtime-настроек; вне загруженных настроек (скрипт/тест) — дефолты.
Отключённый в ``core_connectors`` движок поиска ловится до сети: запрос сразу ``error``
(``error="search_engine_disabled"``).

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
from src.modules.web_search.constants import FETCH_STATUS_PENDING
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.providers import FetchEngine, SearchEngine
from src.modules.web_search.providers import fetch_engines as fetch_engine_registry
from src.modules.web_search.providers import search_engines as search_engine_registry
from src.modules.web_search.providers.request import SearchRequest

_SLOT_POLL_MIN_SECONDS = 0.5
_SLOT_POLL_MAX_SECONDS = 1.5
_PROCESSING_STALE_TTL = timedelta(minutes=15)

# Ссылки на живые фоновые прогоны (``submit``): без них ``asyncio`` может собрать task
# сборщиком до завершения. Снимается в done-callback.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


class Searcher:
    """Фасад сервиса поиска: доступные движки + запуск прогона (блокирующий/фоновый)."""

    @staticmethod
    def search_engines() -> list[str]:
        """Коды доступных (включённых в ``core_connectors``) движков поиска."""
        return search_engine_registry.available_codes()

    @staticmethod
    def fetch_engines() -> list[str]:
        """Коды доступных движков получения контента."""
        return fetch_engine_registry.available_codes()

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
        row, request, engine, fetcher = await Searcher._prepare(
            query,
            search_engine=search_engine,
            fetch_engine=fetch_engine,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        await Searcher._run(row.code, request, engine, fetcher)
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
        row, request, engine, fetcher = await Searcher._prepare(
            query,
            search_engine=search_engine,
            fetch_engine=fetch_engine,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        _schedule(Searcher._run(row.code, request, engine, fetcher))
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
    ) -> tuple[WebSearchQuery, SearchRequest, SearchEngine, FetchEngine]:
        """Резолвит движки (падает ``KeyError`` на неизвестном коде ДО создания строки) и
        создаёт запрос в ``pending`` со снимком обоих движков."""
        request = SearchRequest(
            query=query,
            max_results=max_results if max_results is not None else settings.default_pages(),
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range,
        )
        engine = search_engine_registry.get(search_engine or Searcher._default_search_engine())
        fetcher = fetch_engine_registry.get(fetch_engine or Searcher._default_fetch_engine())
        row = await query_crud.query_create(
            search_engine=engine.code,
            fetch_engine=fetcher.code,
            query=request.query,
            params=request.to_params(),
        )
        return row, request, engine, fetcher

    @staticmethod
    async def _run(
        code: str, request: SearchRequest, engine: SearchEngine, fetcher: FetchEngine
    ) -> None:
        """Прогон запроса ``code``: гейт слота → ``processing`` → поиск → сохранение → фетч → ``done``.

        Сбой движка поиска → запрос ``error`` (без исключения); сбой фетча батча → его страницы ``error``.
        """
        if not engine.available():
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
        await _fetch_pages(fetcher, pending)
        await query_crud.query_finish(code)

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
    ``pending``. Возвращает новые ``pending``-страницы (их дотягивает ``_fetch_pages``);
    уже ``done`` по дедупу — переиспользуются и в список не попадают. Статус запроса тут не
    трогается. Контент движок поиска не отдаёт — это отдельная роль (``_fetch_pages``).
    """
    pending: dict[str, WebSearchPage] = {}
    for result in results:
        page = await page_crud.page_upsert(result["url"], title=result.get("title"))
        if page.status == FETCH_STATUS_PENDING:
            pending[page.code] = page
        await query_result_crud.result_add(
            query_code=query_code,
            page_code=page.code,
            rank=result.get("rank"),
            score=result.get("score"),
            summary=result.get("summary"),
            meta=result.get("meta"),
        )
    return list(pending.values())


async def _fetch_pages(fetcher: FetchEngine, pages: list[WebSearchPage]) -> None:
    """Дотянуть контент ``pending``-страниц: батчи по ``pages_per_request``, семафор."""
    if not pages:
        return
    per_request = fetcher.pages_per_request
    batches = [pages[i:i + per_request] for i in range(0, len(pages), per_request)]
    semaphore = asyncio.Semaphore(settings.fetch_concurrency())

    async def run(batch: list[WebSearchPage]) -> None:
        async with semaphore:
            await page_crud.pages_mark_processing(
                [p.code for p in batch], fetch_engine=fetcher.code
            )
            try:
                contents = await fetcher.fetch_pages([p.url for p in batch])
            except Exception as exc:  # noqa: BLE001 — сбой контента → страницы error (без повторов)
                for page in batch:
                    await page_crud.page_set_error(page.code, error=type(exc).__name__)
                return
            for page in batch:
                body = contents.get(page.url)
                if body:
                    await page_crud.page_set_body(page.code, body=body)
                else:
                    await page_crud.page_set_error(page.code, error="empty")

    await asyncio.gather(*(run(batch) for batch in batches))


__all__ = ["Searcher"]
