"""CRUD ``WebSearchPage`` — контент страницы, дедуп по ``code`` (хеш url).

Ретраев/очереди нет. Машина состояний ``pending → processing → done | error``: страница
создаётся в ``pending``, ``pages_mark_processing`` переводит батч в ``processing`` перед
получением контента, финал — ``page_set_body`` (``done``) или ``page_set_error`` (``error``).
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.sql.selectable import Select

from src.core.database import session_scope
from src.core.utils.date import utc_now
from src.core.utils.hashing import text_hash
from src.modules.web_search.constants import (
    FETCH_STATUS_DONE,
    FETCH_STATUS_ERROR,
    FETCH_STATUS_PENDING,
    FETCH_STATUS_PROCESSING,
)
from src.modules.web_search.models.page import WebSearchPage

def normalize_url(url: str) -> str:
    """Норм. url (по дизайну минимальна): всегда https, хост в нижний регистр, фрагмент ``#…`` отброшен."""
    parts = urlsplit(url.strip())
    return urlunsplit(("https", parts.netloc.lower(), parts.path, parts.query, ""))


def page_code(url: str) -> str:
    """Код страницы — голый 22-hex ``text_hash`` норм. url (детерминирован = ключ дедупа по url).

    web_search коды не типизирует — агентские префиксы живут в модуле research.
    """
    return text_hash(normalize_url(url))


def domain_of(url: str) -> str | None:
    return urlsplit(url).hostname


async def page_upsert(url: str, *, title: str | None = None) -> WebSearchPage:
    """Создать страницу в ``pending`` (или вернуть существующую) по дедуп-коду url.

    ``title`` (заголовок документа из выдачи поиска) проставляется только при создании —
    ``on_conflict_do_nothing`` не перетирает заголовок уже существующей страницы (первый
    нашедший движок задаёт).
    """
    normalized = normalize_url(url)
    code = page_code(url)
    now = utc_now()
    async with session_scope() as s:
        dialect = s.bind.dialect.name if s.bind else "postgresql"
        insert = sqlite_insert if dialect == "sqlite" else pg_insert
        stmt = (
            insert(WebSearchPage)
            .values(
                code=code,
                status=FETCH_STATUS_PENDING,
                domain=domain_of(normalized),
                url=normalized,
                title=title,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["code"])
        )
        await s.execute(stmt)
        row = (
            await s.execute(select(WebSearchPage).where(WebSearchPage.code == code))
        ).scalar_one()
    return row


async def page_get_by_code(code: str) -> WebSearchPage | None:
    async with session_scope() as s:
        return (
            await s.execute(select(WebSearchPage).where(WebSearchPage.code == code))
        ).scalar_one_or_none()


async def pages_mark_processing(codes: list[str], *, fetch_engine: str) -> None:
    """Пометить страницы ``processing`` перед получением контента (батч).

    Снимает движок контента (``fetch_engine``), которым тянем, — на попытке фетча, чтобы
    запись сохранилась и при ``done``, и при ``error`` (движок известен до сети).
    """
    if not codes:
        return
    now = utc_now()
    stmt = (
        update(WebSearchPage)
        .where(WebSearchPage.code.in_(codes))
        .values(status=FETCH_STATUS_PROCESSING, fetch_engine=fetch_engine, updated_at=now)
    )
    async with session_scope() as s:
        await s.execute(stmt)


async def page_set_body(code: str, *, body: str) -> WebSearchPage | None:
    """Сохранить обработанный контент → статус ``done`` (ошибка сброшена)."""
    now = utc_now()
    stmt = (
        update(WebSearchPage)
        .where(WebSearchPage.code == code)
        .values(
            status=FETCH_STATUS_DONE,
            body=body,
            body_hash=text_hash(body),
            fetched_at=now,
            error=None,
            updated_at=now,
        )
        .returning(WebSearchPage)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def page_set_error(code: str, *, error: str | None = None) -> WebSearchPage | None:
    """Терминальная ошибка фетча: статус ``error`` + код ошибки (без повторов)."""
    now = utc_now()
    stmt = (
        update(WebSearchPage)
        .where(WebSearchPage.code == code)
        .values(status=FETCH_STATUS_ERROR, error=error, updated_at=now)
        .returning(WebSearchPage)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


def _page_filtered(
    *, query: str | None, status: str | None, domain: str | None
) -> Select:
    stmt = select(WebSearchPage)
    if query:
        stmt = stmt.where(WebSearchPage.url.ilike(f"%{query}%"))
    if status:
        stmt = stmt.where(WebSearchPage.status == status)
    if domain:
        stmt = stmt.where(WebSearchPage.domain == domain)
    return stmt


# Колонки, по которым допустима сортировка списка (белый список = защита от инъекции:
# неизвестный ключ падает в дефолт ``created_at``). Совпадают с sortable-заголовками фронта.
PAGE_SORT_COLUMNS = {
    "created_at": WebSearchPage.created_at,
    "fetched_at": WebSearchPage.fetched_at,
    "status": WebSearchPage.status,
    "domain": WebSearchPage.domain,
    "url": WebSearchPage.url,
}


async def page_list(
    *,
    query: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> list[WebSearchPage]:
    """Страницы с фильтрами (текст по ``url``, статус, домен), новые сверху.

    Сортировка — по колонке из ``PAGE_SORT_COLUMNS`` (неизвестная → ``created_at``);
    ``code`` — стабильный тайбрейк в ту же сторону (числового id больше нет).
    """
    column = PAGE_SORT_COLUMNS.get(sort_by, WebSearchPage.created_at)
    ascending = sort_dir == "asc"
    order = (
        (column.asc(), WebSearchPage.code.asc())
        if ascending
        else (column.desc(), WebSearchPage.code.desc())
    )
    stmt = (
        _page_filtered(query=query, status=status, domain=domain)
        .order_by(*order)
        .offset(offset)
        .limit(limit)
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def page_count(
    *, query: str | None = None, status: str | None = None, domain: str | None = None
) -> int:
    stmt = _page_filtered(query=query, status=status, domain=domain)
    async with session_scope() as s:
        return (
            await s.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()


__all__ = [
    "page_upsert",
    "page_get_by_code",
    "pages_mark_processing",
    "page_set_body",
    "page_set_error",
    "page_list",
    "page_count",
]
