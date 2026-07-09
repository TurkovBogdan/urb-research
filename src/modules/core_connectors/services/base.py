"""Базовый класс коннектора к внешнему API: общая HTTP-обвязка + гейт по настройкам.

Подкласс объявляет константы поверхности (``BASE_URL``/``API_KEY_FIELD``/``LABEL``, опц.
``TIMEOUT``/``ENABLED_FIELD``) и доменные методы поверх ``_request``/``_post``. Ключ и
тумблер берутся из runtime-настроек core_connectors по именам полей; ответ отдаётся
нативным (доменный маппинг — на стороне потребителя). Один вендор может иметь несколько
поверхностей = несколько подклассов (напр. xAI: инференс + management), у каждой свои
``BASE_URL`` и ``API_KEY_FIELD``.
"""

from __future__ import annotations

from typing import Any, ClassVar

import httpx

from src.modules.core_connectors.services.dto import ConnectorBalance
from src.modules.core_connectors.settings import service_api_key, service_enabled


class ServiceGateway:
    SERVICE: ClassVar[str]  # код коннектора (tavily/firecrawl/xai) — идентификатор в DTO/реестре
    NAME: ClassVar[str]  # человекочитаемое имя коннектора
    DESCRIPTION: ClassVar[str] = ""  # что делает коннектор (для паспорта)
    BASE_URL: ClassVar[str]
    API_KEY_FIELD: ClassVar[str]
    ENABLED_FIELD: ClassVar[str | None] = None  # None → гейт только по наличию ключа
    TIMEOUT: ClassVar[float] = 60.0
    HAS_BALANCE: ClassVar[bool] = False  # умеет ли коннектор отдавать баланс

    def __init__(self, *, timeout: float | None = None) -> None:
        self.timeout = timeout or self.TIMEOUT

    def available(self) -> bool:
        """Не отключён ли коннектор: тумблер on (или его нет). Наличие ключа не проверяет."""
        return self.ENABLED_FIELD is None or service_enabled(self.ENABLED_FIELD)

    async def balance(self) -> ConnectorBalance:
        """Единый вход: остаток/лимиты коннектора в общем ``ConnectorBalance``. Общая логика —
        гейт по ``HAS_BALANCE`` + оркестрация ``_fetch_balance`` → ``_parse_balance``;
        конкретные запрос и маппинг задаёт подкласс."""
        if not self.HAS_BALANCE:
            raise NotImplementedError(f"{self.NAME} не отдаёт баланс")
        return self._parse_balance(await self._fetch_balance())

    async def _fetch_balance(self) -> dict[str, Any]:
        """Сырой ответ баланс-эндпойнта коннектора (подкласс с ``HAS_BALANCE``)."""
        raise NotImplementedError

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Маппинг сырого ответа в ``ConnectorBalance`` (подкласс с ``HAS_BALANCE``)."""
        raise NotImplementedError

    def _ensure_enabled(self) -> None:
        if self.ENABLED_FIELD and not service_enabled(self.ENABLED_FIELD):
            raise RuntimeError(f"{self.NAME} шлюз отключён в настройках")

    def _key(self) -> str:
        key = service_api_key(self.API_KEY_FIELD)
        if not key:
            raise RuntimeError(f"{self.NAME} API-ключ не задан в настройках")
        return key

    def _auth_headers(self) -> dict[str, str]:
        """Заголовки авторизации. По умолчанию ``Authorization: Bearer``; подкласс переопределяет
        под свою схему (напр. Anthropic — ``x-api-key`` + ``anthropic-version``)."""
        return {"Authorization": f"Bearer {self._key()}"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._ensure_enabled()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{endpoint}",
                json=json,
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", endpoint, json=payload)


__all__ = ["ServiceGateway"]
