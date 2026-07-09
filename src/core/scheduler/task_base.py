"""Базовый класс scheduler-задачи.

Лёгкий вариант: только декларативные поля + общий ``register()``. Логика
прогона — в ``handle(ctx)`` наследника.
"""

from __future__ import annotations

from src.core.loggers import get_logger
from src.core.loggers.logger_protocol import CoreLoggerProtocol
from src.core.scheduler.context import TaskContext
from src.core.scheduler.registry import get_registry


class CoreTaskBase:
    """Декларативная база scheduler-задачи.

    Наследник задаёт класс-атрибуты и реализует ``handle``. ``register()``
    собирает регистрацию по этим атрибутам — никакой копипасты вызова
    ``scheduler.register(...)``.
    """

    MODULE: str
    CODE: str
    NAME: str
    DESCRIPTION: str
    SCHEDULE: str | None  # 5-польный cron; None → автозапуск отключён
    TTL: int              # секунды; и timeout хендлера, и TTL task-лока
    ENABLED: bool = True
    USER_REQUEST: bool = False
    SORT: int = 500    # порядок вывода в UI; не влияет на выполнение

    @classmethod
    def logger(cls) -> CoreLoggerProtocol:
        """Tee-логгер задачи: общий канал ``tasks`` + персональный ``tasks/<CODE>``.

        Совпадает с тем, что использует runner и TaskContext — строки из
        handler'а и из внутренних слоёв (импортёры, сервисы) попадают в один
        и тот же файл ``logs/tasks/<CODE>.log``. В отличие от ``ctx.info/warn``
        в БД (``core_tasks_logs``) не пишет — это «техническое» логирование.
        """
        return get_logger("tasks", f"tasks/{cls.CODE}")

    @classmethod
    def register(cls) -> None:
        get_registry().register(
            module=cls.MODULE,
            code=cls.CODE,
            name=cls.NAME,
            description=cls.DESCRIPTION,
            schedule=cls.SCHEDULE,
            handler=cls.handle,
            ttl=cls.TTL,
            enabled=cls.ENABLED,
            user_request=cls.USER_REQUEST,
            sort=cls.SORT,
        )

    @staticmethod
    async def handle(ctx: TaskContext) -> None:
        raise NotImplementedError


__all__ = ["CoreTaskBase"]
