import type { RouteRecordRaw } from 'vue-router'

export const coreMonitoringRoutes: RouteRecordRaw[] = [
  {
    path: '/tasks',
    component: () => import('./views/TasksView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/tasks/:module/:code',
    component: () => import('./views/TaskRunsView.vue'),
    props: true,
    meta: { scroll: 'none', padding: false },
  },
]
