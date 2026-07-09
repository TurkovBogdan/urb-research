"""Шлюз xAI (Grok) — инференс: тонкий типизированный клиент к API, нативные ответы.

Ядро поиска — ``responses()`` (``POST /v1/responses``): агентский цикл на стороне xAI
с server-side инструментами (web_search/x_search/code_execution/collections_search).
Отдельного search-эндпойнта у xAI НЕТ — «поиск» это инференс с ``tools``, а ответ =
синтез модели + URL-источники (в `annotations`/`sources`, топ-уровневого `citations` нет —
см. ``responses()``). Прочие методы — read-only: каталог моделей, tokenize, инфо по ключу.
HTTP-обвязка/ключ — в ``ServiceGateway``. База ``api.x.ai``, аутентификация — Bearer.
Баланс/биллинг живут на **другой** поверхности — см. ``XaiManagementGateway``.

Медиагенерация / voice / files / embeddings намеренно не покрыты — вне задачи поиска контента.
Legacy ``/v1/chat/completions`` (снятый Live Search) не добавлен — только Responses API.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import ConnectorBalance
from src.modules.core_connectors.services.xai.params import (
    XaiResponsesParams,
    XaiTokenizeParams,
)


class XaiGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "xai"
    NAME: ClassVar[str] = "xAI (Grok)"
    DESCRIPTION: ClassVar[str] = "Grok: агентский веб-поиск и поиск по X."
    BASE_URL: ClassVar[str] = "https://api.x.ai"
    TIMEOUT: ClassVar[float] = 300.0  # агентский поиск/multi-agent долгие
    API_KEY_FIELD: ClassVar[str] = "xai_api_key"
    ENABLED_FIELD: ClassVar[str] = "xai_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True  # баланс — с management-поверхности (делегируем)

    async def balance(self) -> ConnectorBalance:
        """Баланс xAI живёт на management-поверхности → делегируем ``XaiManagementGateway``
        (ленивый импорт — избегаем цикла: management тянет этот гейтвей за ``team_id``)."""
        from src.modules.core_connectors.services.xai.management import XaiManagementGateway

        return await XaiManagementGateway().balance()

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
        ``team_id`` нужен методам биллинга ``XaiManagementGateway``. Баланс кредитов сам
        inference-API не отдаёт — смотреть через management API или console.x.ai."""
        return await self._request("GET", "/v1/api-key")


__all__ = ["XaiGateway"]
