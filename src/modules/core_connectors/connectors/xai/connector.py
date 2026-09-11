"""Коннектор xAI (Grok): инференс + биллинг одной записью доступа.

У вендора две поверхности с **разными** хостами и **разными** ключами: инференс
``api.x.ai`` (поле ``api_key``) и биллинг ``management-api.x.ai`` (поле
``management_api_key``, Console → Settings → Management Keys, право *Management Keys
Read*). Это одна учётная запись с двумя секретами, поэтому коннектор один, а какой хост
дёргать — деталь метода.

Ядро поиска — ``responses()`` (``POST /v1/responses``): агентский цикл на стороне xAI с
server-side инструментами (web_search/x_search/code_execution/collections_search).
Отдельного search-эндпойнта у xAI НЕТ — «поиск» это инференс с ``tools``, а ответ =
синтез модели + URL-источники. Прочие методы инференса — read-only: каталог моделей,
tokenize, инфо по ключу.

Медиагенерация / voice / files / embeddings намеренно не покрыты — вне задачи поиска
контента. Legacy ``/v1/chat/completions`` (снятый Live Search) не добавлен.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.core.settings import Field, StrField
from src.modules.core_connectors.connectors.base import HttpConnector
from src.modules.core_connectors.connectors.groups import GROUP_MODELS
from src.modules.core_connectors.connectors.passport import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.connectors.xai.params import (
    XaiResponsesParams,
    XaiTokenizeParams,
)

_CENTS_PER_USD = 100


class XaiConnector(HttpConnector):
    SERVICE: ClassVar[str] = "xai"
    NAME: ClassVar[str] = "xAI (Grok)"
    DESCRIPTION: ClassVar[str] = "Grok: агентский веб-поиск и поиск по X."
    GROUP: ClassVar[str] = GROUP_MODELS
    BASE_URL: ClassVar[str] = "https://api.x.ai"
    MANAGEMENT_URL: ClassVar[str] = "https://management-api.x.ai"
    TIMEOUT: ClassVar[float] = 300.0  # агентский поиск/multi-agent долгие
    FIELDS: ClassVar[tuple[Field, ...]] = (
        StrField(
            key="api_key",
            label="API-ключ",
            description="Секретный ключ доступа к API xAI. Получить: [console.x.ai](https://console.x.ai).",
            secret=True,
        ),
        StrField(
            key="management_api_key",
            label="Management-ключ",
            description="Секретный ключ Management API xAI — для баланса и лимитов трат. Отдельный от основного API-ключа. Создать: [console.x.ai](https://console.x.ai) → Settings → Management Keys.",
            secret=True,
        ),
    )
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

    # ── инференс (api.x.ai) ──────────────────────────────────────────────

    async def responses(self, params: XaiResponsesParams) -> dict[str, Any]:
        """Инференс с агентским поиском (``POST /v1/responses``). Сырой ответ (сверено вживую):
        ``output[]`` = гетерогенный список (`reasoning` / `web_search_call` / финальный
        `message`); текст ответа — в ``output[-1].content[].text`` (тип `output_text`), цитаты —
        рядом в ``.annotations[]`` (`{type:"url_citation", url, start_index, end_index, title}`).
        Все посещённые URL — в ``web_search_call.action.sources[]``. Топ-уровневых ``citations`` /
        ``output_text`` в REST НЕТ (это удобства SDK). ``usage`` несёт ``num_server_side_tools_used``,
        ``server_side_tool_usage_details`` (web_search_calls/…), ``cost_in_usd_ticks``."""
        return await self._post("/v1/responses", params.to_payload())

    async def get_response(self, response_id: str) -> dict[str, Any]:
        """Забрать сохранённый ответ (``GET /v1/responses/{id}``; хранится 30 дней)."""
        return await self._request("GET", f"/v1/responses/{response_id}")

    async def delete_response(self, response_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/v1/responses/{response_id}")

    async def tokenize(self, params: XaiTokenizeParams) -> dict[str, Any]:
        """Токенизировать текст моделью (``POST /v1/tokenize-text``) → ``token_ids[]``."""
        return await self._post("/v1/tokenize-text", params.to_payload())

    async def models(self) -> dict[str, Any]:
        """Каталог моделей ключа с ценами (``GET /v1/models``)."""
        return await self._request("GET", "/v1/models")

    async def language_models(self) -> dict[str, Any]:
        """Языковые модели с полной инфой — модальности/алиасы (``GET /v1/language-models``)."""
        return await self._request("GET", "/v1/language-models")

    async def model(self, model_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v1/models/{model_id}")

    async def api_key_info(self) -> dict[str, Any]:
        """Инфо по API-ключу: статус/права/блокировки + ``team_id`` (``GET /v1/api-key``).
        ``team_id`` нужен методам биллинга — он выводимый, отдельным полем не хранится."""
        return await self._request("GET", "/v1/api-key")

    # ── биллинг (management-api.x.ai, отдельный ключ) ────────────────────

    async def prepaid_balance(self, team_id: str) -> dict[str, Any]:
        """Остаток предоплаты команды (``GET /v1/billing/teams/{team_id}/prepaid/balance``):
        ``total`` (баланс, USD-центы) + ``changes[]`` (история пополнений/списаний)."""
        return await self._management("GET", f"/v1/billing/teams/{team_id}/prepaid/balance")

    async def spending_limits(self, team_id: str) -> dict[str, Any]:
        """Лимиты постоплаты (``GET /v1/billing/teams/{team_id}/postpaid/spending-limits``):
        ``effectiveHardSl`` / ``softSl`` / ``effectiveSl`` (USD-центы)."""
        return await self._management(
            "GET", f"/v1/billing/teams/{team_id}/postpaid/spending-limits"
        )

    async def invoice_preview(self, team_id: str) -> dict[str, Any]:
        """Превью счёта за текущий период (``GET .../postpaid/invoice/preview``):
        ``coreInvoice`` + ``billingCycle`` + ``effectiveSpendingLimit`` (USD-центы)."""
        return await self._management(
            "GET", f"/v1/billing/teams/{team_id}/postpaid/invoice/preview"
        )

    async def _management(self, method: str, endpoint: str) -> dict[str, Any]:
        """Запрос ко второй поверхности вендора: другой хост, другой ключ, та же схема Bearer."""
        key = self.access.require("management_api_key")
        return await self._request(
            method,
            endpoint,
            base_url=self.MANAGEMENT_URL,
            headers={"Authorization": f"Bearer {key}"},
        )

    async def balance(self) -> ConnectorBalance:
        """Баланс живёт на биллинг-поверхности и требует своего ключа. Его отсутствие —
        законная частичная настройка (инференс работает), поэтому это сообщение в DTO,
        а не сбой сервиса."""
        if not self.access.get("management_api_key"):
            return ConnectorBalance(
                service=self.SERVICE,
                name=self.NAME,
                error="Баланс недоступен: не задан management-ключ",
            )
        return await super().balance()

    async def _fetch_balance(self) -> dict[str, Any]:
        """team_id — из инференс-поверхности (`api_key_info`), затем предоплатный баланс."""
        team_id = (await self.api_key_info()).get("team_id")
        if not team_id:
            raise RuntimeError("xAI: team_id недоступен (нет доступа к inference api-key)")
        return await self.prepaid_balance(team_id)

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Предоплатный остаток xAI в USD. ⚠ Знак инвертирован: ``total.val`` отрицателен при
        наличии кредита (пополнения <0, списания >0) → **остаток = −total.val**, из центов в USD."""
        val = (raw.get("total") or {}).get("val")
        amount = -float(val) / _CENTS_PER_USD if val is not None else None
        metrics = [BalanceMetric.money("Баланс", amount)] if amount is not None else []
        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=metrics)


__all__ = ["XaiConnector"]
