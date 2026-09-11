import type { RouteRecordRaw } from 'vue-router'

export const webSearchRoutes: RouteRecordRaw[] = [
  {
    path: '/web-search/queries',
    name: 'web-search-queries',
    component: () => import('./views/QueriesView.vue'),
    meta: { scroll: 'y', title: 'web_search.nav_queries' },
  },
  {
    path: '/web-search/queries/:code',
    name: 'web-search-query',
    component: () => import('./views/QueryView.vue'),
    meta: { scroll: 'y', title: 'web_search.nav_queries' },
  },
  {
    path: '/web-search/pages',
    name: 'web-search-pages',
    component: () => import('./views/PagesView.vue'),
    meta: { scroll: 'y', title: 'web_search.nav_pages' },
  },
  {
    path: '/web-search/pages/:code',
    name: 'web-search-page',
    component: () => import('./views/PageView.vue'),
    meta: { scroll: 'y', title: 'web_search.nav_pages' },
  },
]
