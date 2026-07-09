import type { RouteRecordRaw } from 'vue-router'

export const coreConnectorsRoutes: RouteRecordRaw[] = [
  {
    path: '/connectors',
    component: () => import('./views/ConnectorsView.vue'),
    meta: { scroll: 'y' },
  },
]
