"""Коннектор xAI (Grok): тонкий клиент к API + модели параметров/инструментов + id моделей."""

from src.modules.core_connectors.connectors.xai.connector import XaiConnector
from src.modules.core_connectors.connectors.xai.constants import (
    GROK_BUILD,
    GROK_FLAGSHIP,
    GROK_MULTI_AGENT,
    GROK_NON_REASONING,
    GROK_REASONING,
    MULTI_AGENT_COUNTS,
)
from src.modules.core_connectors.connectors.xai.params import (
    XaiCodeExecutionTool,
    XaiCollectionsSearchTool,
    XaiResponsesParams,
    XaiTokenizeParams,
    XaiWebSearchFilters,
    XaiWebSearchTool,
    XaiXSearchTool,
    json_schema_text,
)

__all__ = [
    "XaiConnector",
    "XaiResponsesParams",
    "XaiTokenizeParams",
    "XaiWebSearchFilters",
    "XaiWebSearchTool",
    "XaiXSearchTool",
    "XaiCodeExecutionTool",
    "XaiCollectionsSearchTool",
    "json_schema_text",
    "GROK_FLAGSHIP",
    "GROK_REASONING",
    "GROK_NON_REASONING",
    "GROK_MULTI_AGENT",
    "GROK_BUILD",
    "MULTI_AGENT_COUNTS",
]
