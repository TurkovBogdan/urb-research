"""Маршруты получения контента: каким движком и через какое подключение качать страницу.

Маршрут — движок контента вместе с подключением его коннектора. Код маршрута в настройках:
``<движок>`` — через первое подключение коннектора, ``<движок>:<id>`` — через конкретное.
В выборе первое подключение стоит за кодом движка, остальные — отдельными вариантами, и только
когда у коннектора подключений два и больше: иначе выбирать не из чего.

Политика — основной маршрут, запасной и их зоны доменов. Страница из зоны идёт только своим
маршрутом (совпала с обеими сторонами — решает более узкая зона, при равных — основной);
остальные — основным, а то, что он не получил, — запасным. Зоны сравниваются в том виде, в
каком хранятся домены страниц: нижний регистр, кириллица в punycode (``.рф`` → ``xn--p1ai``).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from src.core.loggers import get_logger
from src.modules.core_connectors.access.model import AccessRow
from src.modules.core_connectors.service import access_rows, passports
from src.modules.web_search.providers import fetch_engines
from src.modules.web_search.providers.base import FetchEngine

_LOG = get_logger()

ROUTE_SEPARATOR = ":"
NO_FALLBACK = ""


@dataclass(frozen=True)
class FetchRoute:
    """Движок контента и подключение, через которое он пойдёт.

    ``access_id`` — найденное подключение (у кода без id — умолчание коннектора), ``None``,
    если подключения нет. Неготовый маршрут в сеть не ходит: его страницы не получены.
    """

    code: str
    engine: FetchEngine
    access_id: int | None
    ready: bool


@dataclass(frozen=True)
class FetchPolicy:
    primary: FetchRoute | None
    fallback: FetchRoute | None = None
    primary_zones: tuple[str, ...] = ()
    fallback_zones: tuple[str, ...] = ()

    def route_for(self, domain: str | None) -> tuple[FetchRoute | None, bool]:
        """Маршрут страницы и можно ли отдать её запасному, если маршрут её не получит.

        Неготовому запасному не отдаётся ничего: иначе причина, по которой страницу не
        получил основной, подменилась бы недоступностью маршрута, который и не пробовал.
        Свои зоны он держит — их страницы получают видимую ошибку, а не тихий переезд.
        """
        own = normalize_domain(domain) if domain else None
        primary_zone = matching_zone(own, self.primary_zones)
        fallback_zone = matching_zone(own, self.fallback_zones) if self.fallback else None
        if fallback_zone is not None and len(fallback_zone) > len(primary_zone or ""):
            return self.fallback, False
        if primary_zone is not None:
            return self.primary, False
        return self.primary, self.fallback is not None and self.fallback.ready

    @property
    def any_ready(self) -> bool:
        """Есть ли маршрут, которому вообще можно отдать страницу."""
        return any(route is not None and route.ready for route in (self.primary, self.fallback))


def split_route_code(code: str) -> tuple[str, int | None]:
    """``<движок>[:<id подключения>]`` → (движок, id). Неразборчивый код — ``KeyError``."""
    engine_code, separator, access_part = code.partition(ROUTE_SEPARATOR)
    if not separator:
        return engine_code, None
    if not access_part.isdigit():
        raise KeyError(code)
    return engine_code, int(access_part)


def route_code(engine_code: str, access_id: int | None = None) -> str:
    return engine_code if access_id is None else f"{engine_code}{ROUTE_SEPARATOR}{access_id}"


async def resolve_route(code: str) -> FetchRoute:
    """Маршрут по коду из настроек или запроса. Неизвестный движок — ``KeyError``.

    Готовность спрашивается у самого движка — он знает, чем ходит; названное по id
    подключение, которого у коннектора нет, делает маршрут неготовым без вопросов.
    """
    engine_code, access_id = split_route_code(code)
    engine = fetch_engines.get(engine_code)
    row = _connection(await access_rows(connector=engine_code), access_id)
    if access_id is not None and row is None:
        return FetchRoute(code=code, engine=engine, access_id=None, ready=False)
    resolved = row.id if row is not None else None
    return FetchRoute(
        code=code,
        engine=engine,
        access_id=resolved,
        ready=await engine.available(access=resolved),
    )


async def explicit_policy(code: str) -> FetchPolicy:
    """Явно названный маршрут — только он, без запасного и зон. Неизвестный — ``KeyError``."""
    return FetchPolicy(primary=await resolve_route(code))


async def load_policy(
    primary: str,
    fallback: str,
    primary_zones: Iterable[str],
    fallback_zones: Iterable[str],
) -> FetchPolicy:
    """Политика из настроек. Код, указывающий на несуществующий движок, даёт пустой маршрут:
    его страницы не получены, а поиск целиком не падает."""
    return FetchPolicy(
        primary=await _configured_route(primary),
        fallback=await _configured_route(fallback) if fallback != NO_FALLBACK else None,
        primary_zones=normalized_zones(primary_zones),
        fallback_zones=normalized_zones(fallback_zones),
    )


async def route_options() -> list[tuple[str, str]]:
    """Варианты маршрута для настроек: у коннектора с несколькими подключениями — каждое под
    своим именем. Первое стоит за кодом движка: этот код хранится в настройках по умолчанию
    и должен оставаться в списке, сколько бы подключений ни завели."""
    names = {passport.service: passport.name for passport in passports()}
    options: list[tuple[str, str]] = []
    for engine_code in sorted(fetch_engines.codes(), key=lambda code: names.get(code, code)):
        name = names.get(engine_code, engine_code)
        rows = await access_rows(connector=engine_code)
        if len(rows) < 2:
            options.append((engine_code, name))
            continue
        first = _connection(rows, None)
        for place, row in enumerate(rows, start=1):
            title = row.title or f"Подключение {place}"
            code = engine_code if row is first else route_code(engine_code, row.id)
            options.append((code, f"{name} · {title}"))
    return options


async def fallback_route_options() -> list[tuple[str, str]]:
    """Те же варианты и «Нет»: запасной движок необязателен."""
    return [(NO_FALLBACK, "Нет"), *await route_options()]


def normalize_domain(value: str) -> str | None:
    """Домен или зона в форме, в которой хранятся домены страниц: нижний регистр, без ведущих
    ``*`` и точек, кириллица — в punycode. Непригодное значение — ``None``."""
    bare = value.strip().lower().lstrip("*").strip(".")
    if not bare:
        return None
    try:
        return bare.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def normalized_zones(zones: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for zone in zones:
        if not zone.strip():
            continue
        normal = normalize_domain(zone)
        if normal is None:
            _LOG.warning("web_search: zone %r is not a domain — ignored", zone)
            continue
        result.append(normal)
    return tuple(result)


def matching_zone(domain: str | None, zones: Iterable[str]) -> str | None:
    """Самая узкая зона, под которую попадает домен: он сам или его поддомен."""
    if domain is None:
        return None
    hits = [zone for zone in zones if domain == zone or domain.endswith(f".{zone}")]
    return max(hits, key=len, default=None)


def _connection(rows: Sequence[AccessRow], access_id: int | None) -> AccessRow | None:
    """Подключение маршрута: названное по id — или первое (умолчание) коннектора."""
    if access_id is not None:
        return next((row for row in rows if row.id == access_id), None)
    return next((row for row in rows if row.is_default), rows[0] if rows else None)


async def _configured_route(code: str) -> FetchRoute | None:
    try:
        return await resolve_route(code)
    except KeyError:
        _LOG.warning("web_search: fetch route %r points at no engine — skipped", code)
        return None


__all__ = [
    "NO_FALLBACK",
    "ROUTE_SEPARATOR",
    "FetchPolicy",
    "FetchRoute",
    "explicit_policy",
    "fallback_route_options",
    "load_policy",
    "matching_zone",
    "normalize_domain",
    "resolve_route",
    "route_code",
    "route_options",
    "split_route_code",
]
