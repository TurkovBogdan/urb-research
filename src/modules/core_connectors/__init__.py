"""core_connectors — модуль доступов к внешним сервисам.

Наружу смотрит фасадом ``service``: ``open_connector(service)`` отдаёт коннектор,
связанный с записью доступа, либо типизированный отказ. Внутри — ``connectors/`` (что
бывает: паспорта и реестр) и ``access/`` (чем располагаем: записи, их шифрование и кеш).
Модуль самодостаточен: свои таблица, миграция, API и фронт; зависимость всегда в одну
сторону — другие модули зависят от него.
"""

from src.modules.core_connectors.module import CoreConnectorsModule
from src.modules.core_connectors.service import open_connector

__all__ = ["CoreConnectorsModule", "open_connector"]
