"""Стандартные решения для HTTP API ядра: ошибки и обработчики.

Публичная поверхность для модулей:
- ``ApiError`` / ``ErrorBody`` — единый формат и конструкторы ошибок;
- ``Paged`` — конверт списка с пагинацией для read-эндпойнтов;
- ``register_exception_handlers`` — навесить обработчики в ``create_app``.

Ядро НЕ знает о пользователях: принципал и зависимость ``current_user`` живут у
auth-модуля (провайдера auth, если он добавлен); ядро даёт лишь канал
``request.state`` и ``ApiError``.
"""

from __future__ import annotations

from src.core.api.errors import ApiError, ErrorBody
from src.core.api.exceptions import register_exception_handlers
from src.core.api.pagination import Paged

__all__ = [
    "ApiError",
    "ErrorBody",
    "Paged",
    "register_exception_handlers",
]
