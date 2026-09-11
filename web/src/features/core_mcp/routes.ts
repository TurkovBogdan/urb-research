import type { RouteRecordRaw } from 'vue-router'

export const coreMcpRoutes: RouteRecordRaw[] = [
  {
    path: '/mcp-servers',
    name: 'mcp-servers',
    component: () => import('./views/McpServersView.vue'),
    meta: { scroll: 'y', title: 'core_mcp.page.title' },
  },
]
