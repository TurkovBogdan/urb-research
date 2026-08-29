import type { RouteRecordRaw } from 'vue-router'

export const researchRoutes: RouteRecordRaw[] = [
  {
    path: '/research/groups',
    name: 'research-groups',
    component: () => import('./views/GroupsView.vue'),
    meta: { scroll: 'y', title: 'research.nav_groups' },
  },
  {
    path: '/research/researches',
    name: 'research-list',
    component: () => import('./views/ResearchesView.vue'),
    meta: { scroll: 'y', title: 'research.nav' },
  },
  // Адрес полки — тот же сегмент, что и у исследования, разведён префиксом кода:
  // GROUP@… открывает список исследований этой полки, любой другой код — саму карточку
  // исследования. Регистрируется первым: у обоих маршрутов одинаковый вес, побеждает ранний.
  {
    path: '/research/researches/:code(GROUP@.*)',
    name: 'research-group',
    component: () => import('./views/GroupView.vue'),
    meta: { scroll: 'y', title: 'research.group.detail.title' },
  },
  // Деталки — дети общей рамки (`DetailShell`): колонка навигации живёт в родителе и переживает
  // переход с артефакта на артефакт, меняется только содержимое справа. Регистрируется ПОСЛЕ
  // полки: `researches/:code` у них одинакового веса, и побеждает ранний маршрут.
  {
    path: '/research',
    component: () => import('@/layout/templates/DetailShell.vue'),
    children: [
      {
        path: 'researches/:code',
        name: 'research-detail',
        component: () => import('./views/ResearchView.vue'),
        meta: { scroll: 'y', title: 'research.research.detail.title' },
      },
      {
        path: 'areas/:code',
        name: 'research-area',
        component: () => import('./views/AreaView.vue'),
        meta: { scroll: 'y', title: 'research.area.detail.title' },
      },
      {
        path: 'queries/:code',
        name: 'research-query',
        component: () => import('./views/QueryView.vue'),
        meta: { scroll: 'y', title: 'research.query.detail.title' },
      },
      {
        path: 'notes/:code',
        name: 'research-note',
        component: () => import('./views/NoteView.vue'),
        meta: { scroll: 'y', title: 'research.note.detail.title' },
      },
      {
        path: 'sources/:code',
        name: 'research-source',
        component: () => import('./views/SourceView.vue'),
        meta: { scroll: 'y', title: 'research.source.detail.title' },
      },
    ],
  },
]
