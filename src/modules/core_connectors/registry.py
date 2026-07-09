"""Реестр коннекторов: паспорт каждого + опционально баланс.

Держит зарегистрированные коннекторы (по одному на вендор: xAI — это инференс-гейтвей,
баланс он делегирует management-поверхности). ``connectors(with_balance=…)`` отдаёт по
коннектору ``ConnectorView`` = паспорт (``ConnectorInfo``) + опциональный ``ConnectorBalance``
(снимается параллельно только у включённых и умеющих баланс; сбой одного → ``error`` в его
DTO, остальные не падают). Баланс — лишь одна из возможностей реестра, не его суть.
Синглтон ``connectors_registry`` регистрирует дефолтные коннекторы.
"""

from __future__ import annotations

import asyncio

from src.modules.core_connectors.services.anthropic import AnthropicGateway
from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import (
    ConnectorBalance,
    ConnectorInfo,
    ConnectorView,
)
from src.modules.core_connectors.services.firecrawl import FirecrawlGateway
from src.modules.core_connectors.services.openai import OpenAIGateway
from src.modules.core_connectors.services.openrouter import OpenRouterGateway
from src.modules.core_connectors.services.tavily import TavilyGateway
from src.modules.core_connectors.services.xai import XaiGateway


class ConnectorsRegistry:
    def __init__(self) -> None:
        self._connectors: list[ServiceGateway] = []

    def register(self, connector: ServiceGateway) -> None:
        self._connectors.append(connector)

    def all(self) -> list[ServiceGateway]:
        return list(self._connectors)

    def info(self, connector: ServiceGateway) -> ConnectorInfo:
        return ConnectorInfo(
            service=connector.SERVICE,
            name=connector.NAME,
            description=connector.DESCRIPTION,
            enabled=connector.available(),
            has_balance=connector.HAS_BALANCE,
        )

    async def connectors(self, *, with_balance: bool = False) -> list[ConnectorView]:
        """Паспорт каждого коннектора + опционально баланс (у включённых, умеющих его)."""
        return list(
            await asyncio.gather(*(self._view(c, with_balance) for c in self._connectors))
        )

    async def _view(self, connector: ServiceGateway, with_balance: bool) -> ConnectorView:
        info = self.info(connector)
        balance = None
        if with_balance and info.has_balance and info.enabled:
            balance = await self._balance(connector)
        return ConnectorView(info=info, balance=balance)

    @staticmethod
    async def _balance(connector: ServiceGateway) -> ConnectorBalance:
        try:
            return await connector.balance()
        except Exception as exc:  # noqa: BLE001 — сбой одного коннектора не роняет остальных
            return ConnectorBalance(
                service=connector.SERVICE,
                name=connector.NAME,
                error=f"{type(exc).__name__}: {exc}",
            )


connectors_registry = ConnectorsRegistry()
connectors_registry.register(TavilyGateway())
connectors_registry.register(FirecrawlGateway())
connectors_registry.register(XaiGateway())
connectors_registry.register(OpenRouterGateway())
connectors_registry.register(OpenAIGateway())
connectors_registry.register(AnthropicGateway())


__all__ = ["ConnectorsRegistry", "connectors_registry"]
