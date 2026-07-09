import type { RouteRecordRaw } from 'vue-router'

export const coreMcpRoutes: RouteRecordRaw[] = [
  {
    path: '/mcp-servers',
    component: () => import('./views/McpServersView.vue'),
    meta: { scroll: 'y' },
  },
]
