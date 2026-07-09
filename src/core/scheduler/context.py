"""TaskContext — что видит handler задачи."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.crud import tasks as crud_tasks
from src.core.crud import tasks_logs as crud_tasks_logs
from src.core.locks import CoreLock
from src.core.loggers import get_logger
from src.core.models.tasks import CoreTaskLogLevel

_SYS_LEVELS = {
    CoreTaskLogLevel.debug: "debug",
    CoreTaskLogLevel.info: "info",
    CoreTaskLogLevel.warn: "warning",
    CoreTaskLogLevel.error: "error",
}


@dataclass
class TaskContext:
    task_id: int
    module: str
    code: str
    lock: CoreLock  # task-level лок: ключ ``task:{module}:{code}``, owner=task_run:{id}

    @property
    def _file_log(self):
        """Tee-логгер: общий канал ``tasks`` + персональный ``tasks/<code>``."""
        return get_logger("tasks", f"tasks/{self.code}")

    async def set_payload(self, payload: dict[str, Any]) -> None:
        """Записать payload запуска. Ошибки БД глотаются — не должно ронять handler."""
        try:
            await crud_tasks.update_payload(self.task_id, payload)
        except Exception:
            self._file_log.exception("failed to write payload for task %d", self.task_id)

    async def _write_log(self, level: CoreTaskLogLevel, msg: str) -> None:
        """Одна строка в core_tasks_logs + дубль в файловые каналы ``tasks`` и ``tasks/<code>``.

        Каждый вызов — своя сессия с мгновенным коммитом, чтобы лог пережил
        отвал задачи по TTL. Ошибка записи в БД глотается.
        """
        log = self._file_log
        try:
            await crud_tasks_logs.create(
                task_id=self.task_id, level=level, message=msg
            )
        except Exception:
            log.exception("failed to write task log")
        sys_method = getattr(log, _SYS_LEVELS[level])
        sys_method("[%s.%s#%d] %s", self.module, self.code, self.task_id, msg)

    async def debug(self, msg: str, *args: Any) -> None:
        await self._write_log(CoreTaskLogLevel.debug, msg % args if args else msg)

    async def info(self, msg: str, *args: Any) -> None:
        await self._write_log(CoreTaskLogLevel.info, msg % args if args else msg)

    async def warn(self, msg: str, *args: Any) -> None:
        await self._write_log(CoreTaskLogLevel.warn, msg % args if args else msg)

    async def error(self, msg: str, *args: Any) -> None:
        await self._write_log(CoreTaskLogLevel.error, msg % args if args else msg)


__all__ = ["TaskContext"]
