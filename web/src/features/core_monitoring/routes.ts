import type { RouteRecordRaw } from 'vue-router'

export const coreMonitoringRoutes: RouteRecordRaw[] = [
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('./views/TasksView.vue'),
    meta: { scroll: 'y', title: 'core_monitoring.page.title' },
  },
  {
    path: '/tasks/:module/:code',
    name: 'task-runs',
    component: () => import('./views/TaskRunsView.vue'),
    props: true,
    meta: { scroll: 'none', padding: false, title: 'core_monitoring.nav' },
  },
]
