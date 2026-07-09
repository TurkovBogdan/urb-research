"""Core ORM-модели. Импорт регистрирует таблицы в ``Base.metadata``.

``CoreLockRow`` живёт вместе с ``CoreLock`` в ``src.core.locks`` —
импортируем её здесь, чтобы таблица всё равно попала в metadata.
"""

from src.core.locks import CoreLockRow  # noqa: F401
from src.core.models import module_settings  # noqa: F401
from src.core.models import module_state  # noqa: F401
from src.core.models import tasks  # noqa: F401

__all__ = ["module_settings", "module_state", "tasks"]
