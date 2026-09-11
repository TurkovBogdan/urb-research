import type { RouteRecordRaw } from 'vue-router'

export const coreConnectorsRoutes: RouteRecordRaw[] = [
  {
    path: '/integrations',
    name: 'integrations',
    component: () => import('./views/ConnectorsView.vue'),
    meta: { scroll: 'y', title: 'core_connectors.page.title' },
  },
]
