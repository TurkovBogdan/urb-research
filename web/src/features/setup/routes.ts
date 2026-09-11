import type { RouteRecordRaw } from 'vue-router'

export const setupRoutes: RouteRecordRaw[] = [
  {
    path: '/settings/core',
    name: 'settings-core',
    component: () => import('./views/SetupView.vue'),
    meta: { scroll: 'y', title: 'common.nav.server_setup' },
  },
]
