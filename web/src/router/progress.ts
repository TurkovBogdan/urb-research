import { ref, readonly } from 'vue'

// Drives the top loading bar in the content zone (App.vue). Wired into the router
// guards: a navigation that has to wait — auth bootstrap (`ensureReady`) or a
// lazy-chunk `import()` — flips the bar on; it goes back off once the destination
// is resolved (afterEach) or the navigation errors/aborts (onError).
//
// A short show-delay keeps instant (already-cached) navigations from flashing the
// bar: most route swaps resolve in a few ms and never cross the threshold.
const visible = ref(false)
export const navigationLoading = readonly(visible)

const SHOW_DELAY = 140
let showTimer: ReturnType<typeof setTimeout> | null = null

export function startNavigationProgress(): void {
  if (showTimer || visible.value) return
  showTimer = setTimeout(() => {
    showTimer = null
    visible.value = true
  }, SHOW_DELAY)
}

export function stopNavigationProgress(): void {
  if (showTimer) {
    clearTimeout(showTimer)
    showTimer = null
  }
  visible.value = false
}
