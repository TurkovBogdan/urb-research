// Read-only API for the MCP server-surface introspection page (zone `/internal`).
// Lists the modules mounted as MCP servers (`/mcp/<code>`) and, per server, its
// tools + a ready-to-paste stdio connection config. Backend: src/modules/core_mcp.

import { internalApi } from '@/api/client/internal'
import type { McpToolInfo } from '@/components/McpInfoPanel.vue'

const BASE = '/core-mcp'

export interface McpServerSummary {
  code: string
  name: string
  version: string | null
  instructions: string | null
  tool_count: number
}

export interface McpServerDetail {
  code: string
  name: string
  version: string | null
  instructions: string | null
  tools: McpToolInfo[]
  // Единый stdio-конфиг (Claude Desktop и Claude Code — одинаково через обёртку).
  connection_config: string
}

export function listMcpServers(): Promise<McpServerSummary[]> {
  return internalApi.get<McpServerSummary[]>(`${BASE}/servers`)
}

export function getMcpServer(code: string): Promise<McpServerDetail> {
  return internalApi.get<McpServerDetail>(`${BASE}/servers/${encodeURIComponent(code)}`)
}
