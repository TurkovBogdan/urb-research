import type { RouteRecordRaw } from 'vue-router'

export const researchRoutes: RouteRecordRaw[] = [
  {
    path: '/research/researches',
    component: () => import('./views/ResearchesView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/research/researches/:code',
    component: () => import('./views/ResearchView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/research/areas/:code',
    component: () => import('./views/AreaView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/research/queries/:code',
    component: () => import('./views/QueryView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/research/notes/:code',
    component: () => import('./views/NoteView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/research/sources/:code',
    component: () => import('./views/SourceView.vue'),
    meta: { scroll: 'y' },
  },
]
