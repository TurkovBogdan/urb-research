"""Навешивание guard'ов на маршруты и их применение — три стадии одного слоя.

- **Объявление** — ``@guard("вид", *аргументы)`` кладёт на функцию-эндпоинт
  непрозрачное правило ``(вид, *аргументы)`` (только данные, ядро их не парсит);
  ``guard_rules``/``is_allow_all``/``is_deny_all`` читают эти метки обратно.
- **Исполнение** — ``make_zone_guard`` строит ``zone_guard`` (зон-зависимость): на
  каждый запрос ``allow_all``/``deny_all`` он знает сам, остальные виды резолвит по
  реестру (умолчание зоны + виды меток, по порядку, первый ``raise`` останавливает).
- **Валидация** — ``validate_guard_rules`` на сборке проверяет, что все упомянутые
  виды зарегистрированы (декоратор сам не может — отрабатывает при импорте, до реестра).
"""

from __future__ import annotations

from fastapi import Request

from src.core.router.guards.registry import GuardFn, GuardRegistry


def guard(kind: str, *args: str):
    """Навесить на эндпоинт правило ``(вид, *аргументы)``. Ядро его не интерпретирует."""

    def deco(fn):
        fn.__guards__ = (*getattr(fn, "__guards__", ()), (kind, *args))
        return fn

    return deco


def guard_rules(endpoint) -> tuple:
    """Все правила маршрута: кортеж ``(вид, *аргументы)``."""
    return getattr(endpoint, "__guards__", ())


def is_allow_all(endpoint) -> bool:
    return ("allow_all",) in guard_rules(endpoint)


def is_deny_all(endpoint) -> bool:
    return ("deny_all",) in guard_rules(endpoint)


def make_zone_guard(registry: GuardRegistry, default: list[str]) -> GuardFn:
    """Зон-зависимость: ``default`` — умолчательные виды зоны (default-on).

    ``allow_all``/``deny_all`` исполняются сразу; иначе прогоняем умолчание зоны +
    виды меток по порядку, каждый — через реестр. Пусто ⇒ ``deny_all`` (фолбэк).
    """

    async def zone_guard(request: Request) -> None:
        endpoint = request.scope["endpoint"]
        if is_allow_all(endpoint):
            return await registry.resolve("allow_all")(request)
        if is_deny_all(endpoint):
            return await registry.resolve("deny_all")(request)
        kinds = (*default, *(rule[0] for rule in guard_rules(endpoint)))
        for kind in kinds or ("deny_all",):
            await registry.resolve(kind)(request)

    return zone_guard


def validate_guard_rules(app, registry: GuardRegistry, *, defaults=()) -> None:
    """Проверить на сборке, что все виды guard'ов зарегистрированы.

    Сканирует виды в ``@guard(...)`` на всех маршрутах ``app`` и умолчательные
    виды зоны (``defaults``). Незарегистрированный вид ⇒ ``RuntimeError`` на
    старте («guard должен быть зарегистрирован до использования»). Декоратор
    отрабатывает при импорте, поэтому проверка — здесь, после сбора реестра.
    """
    unknown: list[str] = []
    for kind in defaults:
        if not registry.has(kind):
            unknown.append(f'default "{kind}"')
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        for rule in guard_rules(endpoint):
            if not registry.has(rule[0]):
                path = getattr(route, "path", "?")
                unknown.append(f'@guard("{rule[0]}") @ {path}')
    if unknown:
        raise RuntimeError(
            "guard-виды не зарегистрированы в реестре: " + ", ".join(unknown)
        )


__all__ = [
    "guard",
    "guard_rules",
    "is_allow_all",
    "is_deny_all",
    "make_zone_guard",
    "validate_guard_rules",
]
