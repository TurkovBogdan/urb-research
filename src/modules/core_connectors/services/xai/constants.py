"""Идентификаторы моделей и режимов xAI — чтобы потребитель не хардкодил строки.

Сверено вживую через ``XaiGateway.models()``/``model()`` (2026-07-05). Канонические id —
pinned-версии (``*-0309``, ротируются); стабильные — алиасы (``grok-4.20-multi-agent`` →
``grok-4.20-multi-agent-0309``, ``grok-4.3`` → ``grok-4.3-latest``/``grok-latest``).
Актуальный каталог/цены — ``models()`` / docs.x.ai/developers/models.
"""

from __future__ import annotations

GROK_FLAGSHIP = "grok-4.3"  # рекомендуемый для чата/кодинга, 1M контекст
GROK_REASONING = "grok-4.20-0309-reasoning"
GROK_NON_REASONING = "grok-4.20-0309-non-reasoning"
GROK_MULTI_AGENT = "grok-4.20-multi-agent"  # deep research (agent_count 4|16), 2M контекст
GROK_BUILD = "grok-build-0.1"  # компактная, 256k контекст

MULTI_AGENT_COUNTS = (4, 16)  # быстрый/фокусный vs глубокий/многогранный

__all__ = [
    "GROK_FLAGSHIP",
    "GROK_REASONING",
    "GROK_NON_REASONING",
    "GROK_MULTI_AGENT",
    "GROK_BUILD",
    "MULTI_AGENT_COUNTS",
]
