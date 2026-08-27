import type { RouteRecordRaw } from 'vue-router'

export const settingsRoutes: RouteRecordRaw[] = [
  {
    path: '/settings/interface',
    name: 'settings-interface',
    component: () => import('./views/InterfaceView.vue'),
    meta: { scroll: 'y', title: 'settings.interface.page.title' },
  },
  {
    path: '/settings/modules',
    name: 'settings-modules',
    component: () => import('./views/SettingsView.vue'),
    meta: { scroll: 'y', title: 'settings.page.title' },
  },
]
