"""Кодек кодов research: снятие префикса + отказ коду снятого формата.

Формат стандартизирован жёстко — код в 22 знака не резолвится никуда. Голое «не найдено» этого
не объясняет, поэтому граница отвечает текстом про формат (``RETIRED_CODE_REFUSAL``). Коды
web_search (``SEARCH@`` / ``PAGE@``) длину не меняли и через этот кодек не ходят.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.codes import (
    RETIRED_CODE_LEN,
    bare_code,
    checked_code,
    strip_prefix,
)
from src.modules.research.constants import CODE_LEN

CURRENT = "a" * CODE_LEN
RETIRED = "b" * RETIRED_CODE_LEN


@pytest.mark.pure
def test_current_code_passes_with_and_without_its_prefix():
    assert checked_code(f"AREA@{CURRENT}") == f"AREA@{CURRENT}"
    assert bare_code(f"AREA@{CURRENT}") == CURRENT
    assert bare_code(CURRENT) == CURRENT


@pytest.mark.pure
@pytest.mark.parametrize("code", [f"RESEARCH@{RETIRED}", RETIRED])
def test_retired_code_is_refused_by_naming_the_format(code):
    with pytest.raises(ValueError, match="retired 22-char format"):
        checked_code(code)
    with pytest.raises(ValueError, match="retired 22-char format"):
        bare_code(code)


@pytest.mark.pure
def test_an_empty_code_stays_empty():
    assert bare_code(None) is None
    assert bare_code("") == ""


@pytest.mark.pure
def test_a_long_tail_that_is_not_hex_is_not_a_retired_code():
    """Отказ смотрит на алфавит, а не только на длину — иначе им накрыло бы чужие строки."""
    not_a_hash = "z" * RETIRED_CODE_LEN

    assert bare_code(f"AREA@{not_a_hash}") == strip_prefix(f"AREA@{not_a_hash}")


@pytest.mark.db
async def test_mcp_tool_answers_a_retired_code_with_the_format(call):
    with pytest.raises(ToolError, match="retired 22-char format"):
        await call("research_get", research_code=f"RESEARCH@{RETIRED}")
