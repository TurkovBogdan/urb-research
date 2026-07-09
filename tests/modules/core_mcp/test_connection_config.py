"""core_mcp: генерация stdio-конфига подключения (в т.ч. проброс MCP_TOKEN)."""

from __future__ import annotations

import json

import pytest

from src.modules.core_mcp.api import _stdio_config


@pytest.mark.pure
def test_stdio_config_embeds_token_when_set():
    config = json.loads(_stdio_config("research", pin_code=False, token="secret-xyz"))
    server = config["mcpServers"]["research"]
    assert server["env"]["MCP_TOKEN"] == "secret-xyz"
    assert "MCP_STDIO_CODE" not in server["env"]  # один сервер → код не пинуем


@pytest.mark.pure
def test_stdio_config_no_env_without_token_single_server():
    server = json.loads(_stdio_config("research", pin_code=False, token=""))["mcpServers"]["research"]
    assert "env" not in server  # ни токена, ни пина — env не нужен


@pytest.mark.pure
def test_stdio_config_pins_code_and_token_together():
    server = json.loads(_stdio_config("research", pin_code=True, token="t"))["mcpServers"]["research"]
    assert server["env"] == {"MCP_TOKEN": "t", "MCP_STDIO_CODE": "research"}
