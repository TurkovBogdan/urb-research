"""Runtime-настройки самого модуля: бюджет на опрос сервисов.

Кредов здесь больше нет — они переехали в таблицу записей доступа (динамический реестр и
статическая схема несовместимы: схемы регистрируются раньше любого ``configure()``, store
кодогенерён по схеме, а поле-выбор валидирует по кортежу времени сборки). В схеме остаются
только собственные ручки модуля.

Обе — про время: опрос баланса не боевой вызов, и ждать его столько же, сколько скрейпа
страницы, незачем. Таймаут ограничивает один вызов, дедлайн — всю выдачу списка; иначе
одного медленного сервиса хватает, чтобы положить страницу целиком.
"""

from __future__ import annotations

from src.core.settings import IntField, get_module_store

MODULE = "core_connectors"

BALANCE_TIMEOUT_DEFAULT = 15
POLL_DEADLINE_DEFAULT = 25

_POLL = "Опрос сервисов"

SCHEMA = (
    IntField(
        key="balance_timeout",
        label="Таймаут запроса баланса, с",
        description="Сколько ждать ответа одного сервиса при снятии баланса или проверке.",
        default_=BALANCE_TIMEOUT_DEFAULT,
        min=1,
        max=120,
        group=_POLL,
    ),
    IntField(
        key="poll_deadline",
        label="Дедлайн опроса, с",
        description="Общий потолок времени на опрос всех интеграций страницы; не успевшие отдают ошибку в своей карточке.",
        default_=POLL_DEADLINE_DEFAULT,
        min=1,
        max=300,
        group=_POLL,
    ),
)


def _setting(field_key: str, fallback: int) -> int:
    """Настройка из store; ``fallback``, если store ещё не загружен (скрипт/тест)."""
    try:
        return getattr(get_module_store(MODULE), field_key)
    except RuntimeError:
        return fallback


def balance_timeout() -> int:
    """Потолок времени на один вызов баланса/проверки."""
    return _setting("balance_timeout", BALANCE_TIMEOUT_DEFAULT)


def poll_deadline() -> int:
    """Потолок времени на опрос всех коннекторов сразу."""
    return _setting("poll_deadline", POLL_DEADLINE_DEFAULT)


__all__ = ["SCHEMA", "MODULE", "balance_timeout", "poll_deadline"]
