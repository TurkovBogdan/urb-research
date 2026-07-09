"""Модели параметров запросов xAI — Responses API + tokenize.

xAI принимает поля в snake_case (OpenAI-совместимо), поэтому алиасы не нужны:
``to_payload()`` = ``model_dump(exclude_none=True)``, незаданные поля опускаются —
дефолты применяет сам xAI. Формы по докам docs.x.ai. Ответ шлюз отдаёт нативным
(маппинг под домен — на стороне потребителя).

Server-side инструменты Responses API моделируются классами ``Xai*Tool`` (общий базовый
``_XaiTool`` с ``extra="allow"`` — пропускает несверённые поля насквозь). В
``XaiResponsesParams.tools`` они сериализуются через ``SerializeAsAny`` (по фактическому
типу), поэтому в список можно класть и типизированные модели инструментов, и сырые dict.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, SerializeAsAny


class _XaiParams(BaseModel):
    def to_payload(self) -> dict[str, Any]:
        """JSON-тело запроса: только явно заданные поля (``None`` опускаются)."""
        return self.model_dump(exclude_none=True)


class _XaiTool(_XaiParams):
    """База server-side инструмента Responses API — ``extra="allow"`` для проброса
    несверённых полей; конкретный инструмент задаёт ``type`` и свои поля."""

    model_config = ConfigDict(extra="allow")

    type: str


class XaiWebSearchFilters(_XaiParams):
    allowed_domains: list[str] | None = None  # ≤5; нельзя вместе с excluded_domains
    excluded_domains: list[str] | None = None  # ≤5


class XaiWebSearchTool(_XaiTool):
    """Веб-поиск + браузинг страниц в реальном времени (``type="web_search"``)."""

    type: str = "web_search"
    filters: XaiWebSearchFilters | None = None
    enable_image_search: bool | None = None  # искать картинки, вставлять ![](url) в ответ
    enable_image_understanding: bool | None = None  # анализ найденных картинок (view_image)
    # NB: search_context_size на вход НЕ принимается (400 «Argument not supported»);
    # оно лишь в эхо ответа как дефолт xAI (сверено вживую 2026-07-05).


class XaiXSearchTool(_XaiTool):
    """Поиск по X/Twitter: keyword/semantic/user/thread (``type="x_search"``).
    В ответе `output[]` вызов всплывает блоком `custom_tool_call` (не `x_search_call`);
    счётчик — `usage.server_side_tool_usage_details.x_search_calls`."""

    type: str = "x_search"
    allowed_x_handles: list[str] | None = None  # ≤20
    excluded_x_handles: list[str] | None = None  # ≤20
    from_date: str | None = None  # ISO8601 YYYY-MM-DD
    to_date: str | None = None  # ISO8601 YYYY-MM-DD
    enable_image_understanding: bool | None = None
    enable_video_understanding: bool | None = None


class XaiCodeExecutionTool(_XaiTool):
    """Исполнение Python на стороне сервера (``type="code_execution"``)."""

    type: str = "code_execution"


class XaiCollectionsSearchTool(_XaiTool):
    """RAG-поиск по загруженным коллекциям (``type="collections_search"``).
    Точные поля не сверены живьём — прочие ключи проходят насквозь (``extra="allow"``)."""

    type: str = "collections_search"
    collection_ids: list[str] | None = None


class XaiResponsesParams(_XaiParams):
    model: str
    input: str | list[dict[str, Any]]  # промпт-строка ИЛИ список message-объектов
    tools: list[SerializeAsAny[_XaiTool]] | None = None  # server-side инструменты/функции
    tool_choice: str | dict[str, Any] | None = None  # auto | none | required | конкретный
    instructions: str | None = None  # системная инструкция
    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    reasoning: dict[str, Any] | None = None  # напр. {"effort": "high"}
    text: dict[str, Any] | None = None  # формат вывода; строгий JSON → json_schema_text(...)
    agent_count: int | None = None  # только для multi-agent модели: 4 | 16 (сверено вживую)
    previous_response_id: str | None = None  # stateful-цепочка вместо пересылки истории
    store: bool | None = None  # хранить ответ для последующего GET (по умолчанию xAI хранит 30д)
    background: bool | None = None  # async-обработка (ответ сразу, статус — через get_response)
    include: list[str] | None = None  # напр. ["reasoning.encrypted_content"]


class XaiTokenizeParams(_XaiParams):
    text: str
    model: str


def json_schema_text(name: str, schema: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
    """Собрать значение ``text`` для строгого structured output Responses API →
    ``{"format": {"type": "json_schema", "name", "strict", "schema"}}``. Кладётся в
    ``XaiResponsesParams.text``. Требования xAI к схеме (strict): root = ``object``, все
    свойства перечислены в ``required``, ``additionalProperties: false``. Поддерживается
    вместе с инструментами (`web_search` и др.) на семействе Grok-4."""
    return {"format": {"type": "json_schema", "name": name, "strict": strict, "schema": schema}}


__all__ = [
    "XaiWebSearchFilters",
    "XaiWebSearchTool",
    "XaiXSearchTool",
    "XaiCodeExecutionTool",
    "XaiCollectionsSearchTool",
    "XaiResponsesParams",
    "XaiTokenizeParams",
    "json_schema_text",
]
