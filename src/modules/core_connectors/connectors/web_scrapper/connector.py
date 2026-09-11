"""Коннектор daemon-web-scrapper: тонкий клиент к резиденту локального браузерного скрейпера.

Локальный демон `daemon-web-scrapper` (браузерный скрейпер, порт 19020) отдаёт главный
контент страницы как markdown. Метод принимает модель параметров, POST'ит её тело на
``/api/1.0/scrap-batch`` и возвращает НАТИВНЫЙ JSON-ответ демона без доменного маппинга.

Отличий от облачных коннекторов два, и оба идут из паспорта. Адрес демона — **поле записи**,
а не константа: демон локальный и переезжает вместе с установкой. Токен **необязателен**:
при пустом ``SCRAPER_API_KEY`` демон отключает авторизацию, поэтому пустой токен — законная
конфигурация, а не «не настроено».

Баланса у демона нет, поэтому балансовой пробы (которой живут остальные) тут не существует —
``check()`` переопределён на проверку достижимости: коннектор без баланса не должен
оставаться и без проверки.
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

import httpx

from src.core.settings import Field, StrField
from src.modules.core_connectors.connectors.base import HttpConnector
from src.modules.core_connectors.connectors.groups import GROUP_SCRAPING
from src.modules.core_connectors.connectors.passport import ConnectorCheck
from src.modules.core_connectors.connectors.web_scrapper.params import (
    WebScrapperScrapBatchParams,
)

_DEFAULT_URL = "http://127.0.0.1:19020"
_CHECK_TIMEOUT = 5.0


class WebScrapperConnector(HttpConnector):
    SERVICE: ClassVar[str] = "web_scrapper"
    NAME: ClassVar[str] = "UroborosWebScrapper"
    DESCRIPTION: ClassVar[str] = "Локальный сервис скрапинга сайтов через анонимный браузер."
    GROUP: ClassVar[str] = GROUP_SCRAPING
    BASE_URL: ClassVar[str] = _DEFAULT_URL
    TIMEOUT: ClassVar[float] = 180.0  # = DAEMON_REQUEST_TIMEOUT_SECONDS: покрывает холодный старт браузера
    HAS_BALANCE: ClassVar[bool] = False
    FIELDS: ClassVar[tuple[Field, ...]] = (
        StrField(
            key="base_url",
            label="Адрес демона",
            description="Где слушает UroborosWebScrapper.",
            default_=_DEFAULT_URL,
        ),
        StrField(
            key="api_key",
            label="Токен",
            description="Bearer-токен демона (SCRAPER_API_KEY). Оставьте пустым, если у демона авторизация отключена.",
            secret=True,
        ),
    )

    @property
    def base_url(self) -> str:
        return self.access.get("base_url") or _DEFAULT_URL

    def _auth_headers(self) -> dict[str, str]:
        """Bearer только при заданном токене; пустой = демон без авторизации (локальный dev)."""
        key = self.access.get("api_key")
        return {"Authorization": f"Bearer {key}"} if key else {}

    async def check(self) -> ConnectorCheck:
        """Достижим ли демон. Код ответа не важен — важно, что на порту кто-то отвечает
        по HTTP: маршрута здоровья у демона нет, а 404 от него — уже признак жизни."""
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=_CHECK_TIMEOUT) as client:
                await client.get(self.base_url, headers=self._auth_headers())
        except httpx.HTTPError as exc:
            return ConnectorCheck(ok=False, error=f"{type(exc).__name__}: {exc}")
        return ConnectorCheck(ok=True, latency_ms=int((time.monotonic() - started) * 1000))

    async def scrap_batch(self, params: WebScrapperScrapBatchParams) -> dict[str, Any]:
        """Батч-скрейп url'ов: нативный ответ ``{results: [<scrap>], elapsed_ms}``."""
        return await self._post("/api/1.0/scrap-batch", params.to_payload())


__all__ = ["WebScrapperConnector"]
