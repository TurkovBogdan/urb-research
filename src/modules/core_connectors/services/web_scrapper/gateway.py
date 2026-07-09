"""Шлюз daemon-web-scrapper: тонкий клиент к резиденту локального браузерного скрейпера.

Локальный демон `daemon-web-scrapper` (браузерный скрейпер, порт 19020) отдаёт главный
контент страницы как markdown. Метод принимает модель параметров, POST'ит её тело на
``/api/1.0/scrap-batch`` и возвращает НАТИВНЫЙ JSON-ответ демона без доменного маппинга —
форму под потребителя строит сам потребитель. HTTP-обвязка/тумблер — в ``ServiceGateway``.

Аутентификация опциональна: демон принимает ``Authorization: Bearer <token>``, но при пустом
``SCRAPER_API_KEY`` авторизацию отключает (локальный dev). Поэтому ``_auth_headers`` шлёт Bearer
только когда ключ задан в настройках, иначе идёт без заголовка (а не падает, как база). Баланса
у демона нет (``HAS_BALANCE`` = False) — в реестр коннекторов не регистрируется.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.web_scrapper.params import (
    WebScrapperScrapBatchParams,
)
from src.modules.core_connectors.settings import service_api_key


class WebScrapperGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "web_scrapper"
    NAME: ClassVar[str] = "daemon-web-scrapper"
    DESCRIPTION: ClassVar[str] = "Браузерный скрейпинг страниц в markdown локальным демоном."
    BASE_URL: ClassVar[str] = "http://127.0.0.1:19020"
    TIMEOUT: ClassVar[float] = 180.0  # = DAEMON_REQUEST_TIMEOUT_SECONDS: покрывает холодный старт браузера
    API_KEY_FIELD: ClassVar[str] = "web_scrapper_api_key"
    ENABLED_FIELD: ClassVar[str] = "web_scrapper_gateway_enabled"

    def _auth_headers(self) -> dict[str, str]:
        """Bearer только при заданном ключе; пустой ключ = демон без авторизации (локальный dev)."""
        key = service_api_key(self.API_KEY_FIELD)
        return {"Authorization": f"Bearer {key}"} if key else {}

    async def scrap_batch(self, params: WebScrapperScrapBatchParams) -> dict[str, Any]:
        """Батч-скрейп url'ов: нативный ответ ``{results: [<scrap>], elapsed_ms}``."""
        return await self._post("/api/1.0/scrap-batch", params.to_payload())


__all__ = ["WebScrapperGateway"]
