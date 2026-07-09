"""Модуль ``core_setup``: страница настроек, редактирующая ``.env`` + рестарт.

Слой ENV/``Config`` (deploy-time), НЕ рантайм-настройки (``core_modules_settings``).
Правка ``.env`` применяется перезапуском процесса. Без БД/задач — только internal-API.
"""

from __future__ import annotations

from typing import ClassVar

from src.core.module import Module
from src.modules.core_setup.api import router


class CoreSetupModule(Module):
    name: ClassVar[str] = "core_setup"
    description: ClassVar[str] = "Редактирование ENV/.env (параметры деплоя) и перезапуск процесса."
    internal_router = router
    internal_router_prefix = "/core/setup"
