import type { RouteRecordRaw } from 'vue-router'

export const aboutRoutes: RouteRecordRaw[] = [
  {
    path: '/about',
    name: 'about',
    component: () => import('./views/AboutView.vue'),
    meta: { scroll: 'y', title: 'about.page.title' },
  },
]
