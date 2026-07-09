import { createRouter, createWebHistory } from 'vue-router'

import { setupGuards } from './guards'
import { designSystemRoutes } from './design-system'
import { coreConnectorsRoutes } from '../features/core_connectors/routes'
import { coreMcpRoutes } from '../features/core_mcp/routes'
import { coreMonitoringRoutes } from '../features/core_monitoring/routes'
import { researchRoutes } from '../features/research/routes'
import { settingsRoutes } from '../features/settings/routes'
import { setupRoutes } from '../features/setup/routes'
import { webSearchRoutes } from '../features/web_search/routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/home' },
    {
      path: '/home',
      component: () => import('../views/HomeView.vue'),
      meta: { scroll: 'y' },
    },
    ...designSystemRoutes,
    ...coreMcpRoutes,
    ...coreConnectorsRoutes,
    ...coreMonitoringRoutes,
    ...settingsRoutes,
    ...setupRoutes,
    ...webSearchRoutes,
    ...researchRoutes,
    // Catch-all 404 — kept LAST so it can't shadow any route declared above it.
    // Renders the 404 inside the app shell.
    {
      path: '/:pathMatch(.*)*',
      component: () => import('../views/errors/NotFoundView.vue'),
      meta: { scroll: 'none', padding: false },
    },
  ],
})

setupGuards(router)

export default router
