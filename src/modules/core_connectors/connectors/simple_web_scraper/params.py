"""Модели параметров simple-web-scraper — батч-скрейп страниц (`/api/1.0/scrap/batch`).

``to_payload()`` даёт JSON-тело, опуская незаданные (``None``) поля — дефолты
(флаги загрузки, бюджет времени) применяет сам демон (`simple-web-scraper/src/schemas.py`).
Только параметры запроса; ответ шлюз отдаёт нативным (доменный маппинг — на стороне
потребителя).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SimpleWebScraperScrapBatchParams(BaseModel):
    """Батч-скрейп нескольких url в одном вызове (грузятся параллельно на стороне демона).
    Опции общие для всех url; без флагов страница грузится до ``DOMContentLoaded``."""

    urls: list[str]
    use_idle: bool | None = None  # ждать сетевого простоя: SPA и страницы, дорисованные JS
    use_scroll: bool | None = None  # после загрузки прокрутить до конца: ленивые ленты
    timeout: int | None = None  # 1–60 целых сек на всю загрузку вместе с прокруткой

    def to_payload(self) -> dict[str, Any]:
        """JSON-тело запроса: только явно заданные поля (``None`` опускаются)."""
        return self.model_dump(exclude_none=True)


__all__ = ["SimpleWebScraperScrapBatchParams"]
