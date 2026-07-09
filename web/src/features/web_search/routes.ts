import type { RouteRecordRaw } from 'vue-router'

export const webSearchRoutes: RouteRecordRaw[] = [
  {
    path: '/web-search/queries',
    component: () => import('./views/QueriesView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/web-search/queries/:code',
    component: () => import('./views/QueryView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/web-search/pages',
    component: () => import('./views/PagesView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/web-search/pages/:code',
    component: () => import('./views/PageView.vue'),
    meta: { scroll: 'y' },
  },
]
