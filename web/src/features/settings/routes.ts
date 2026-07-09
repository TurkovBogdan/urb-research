import type { RouteRecordRaw } from 'vue-router'

export const settingsRoutes: RouteRecordRaw[] = [
  {
    path: '/settings/modules',
    component: () => import('./views/SettingsView.vue'),
    meta: { scroll: 'y' },
  },
]
