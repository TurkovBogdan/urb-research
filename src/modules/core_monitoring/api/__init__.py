"""Зон-роутер модуля core_monitoring (зона internal, без собственного префикса).

Пока одна поверхность — ``/tasks`` (scheduler-задачи: список, запуски, логи). Модуль
не задаёт ``internal_router_prefix``, и агрегатор не навешивает prefix — корень пути
(``/tasks``) прописан в самих маршрутах под-роутера.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.core_monitoring.api.tasks import router as tasks_router

internal_router = APIRouter()
internal_router.include_router(tasks_router, tags=["tasks"])

__all__ = ["internal_router"]
