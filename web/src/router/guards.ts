import type { Router } from 'vue-router'
import { startNavigationProgress, stopNavigationProgress } from './progress'
import { dismissHoverTooltips } from './overlays'
import { recordNavigation } from '@/composables/useNavigationHistory'

export function setupGuards(router: Router): void {
  router.beforeEach(() => {
    // Close any hover tooltip before KeepAlive deactivates its page and orphans the
    // teleported overlay (the activator's mouseleave never fires on a navigating click).
    dismissHoverTooltips()

    // Arm the content-zone loading bar; the show-delay swallows instant swaps.
    startNavigationProgress()
    return true
  })

  // Destination resolved (incl. lazy chunk loaded) — drop the bar.
  router.afterEach((_to, from) => {
    recordNavigation(from)
    stopNavigationProgress()
  })
  // Aborted/failed navigation never reaches afterEach — clear the bar here too.
  router.onError(() => stopNavigationProgress())
}
