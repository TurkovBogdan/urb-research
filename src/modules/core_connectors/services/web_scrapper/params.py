"""Модели параметров daemon-web-scrapper — батч-скрейп страниц (`/api/1.0/scrap-batch`).

``to_payload()`` даёт JSON-тело, опуская незаданные (``None``) поля — дефолты
(режим, таймауты) применяет сам демон (`daemon-web-scrapper/src/schemas.py`). Только
параметры запроса; ответ шлюз отдаёт нативным (доменный маппинг — на стороне потребителя).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WebScrapperScrapBatchParams(BaseModel):
    """Батч-скрейп нескольких url в одном вызове (грузятся параллельно на стороне демона).
    Опции общие для всех url. ``mode``: get | browser_load | browser_idle | browser_scroll."""

    urls: list[str]
    mode: str | None = None
    timeout: float | None = None  # сек: жёсткий потолок фазы загрузки страницы
    load_timeout: float | None = None
    scroll_timeout: float | None = None  # для mode=browser_scroll

    def to_payload(self) -> dict[str, Any]:
        """JSON-тело запроса: только явно заданные поля (``None`` опускаются)."""
        return self.model_dump(exclude_none=True)


__all__ = ["WebScrapperScrapBatchParams"]
