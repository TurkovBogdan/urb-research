"""Конверт списка с пагинацией — общая форма ответа списочных read-эндпойнтов.

``Paged[T]`` оборачивает страницу элементов (``items``) метаданными пагинации
(``total`` — всего строк под фильтром, ``page``/``page_size`` — текущее окно). Модули
отдают списки в этой форме, фронт-клиент разбирает её единообразно.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paged(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


__all__ = ["Paged"]
