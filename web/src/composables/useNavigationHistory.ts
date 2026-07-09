import type { RouteLocationNormalized, RouteLocationRaw, Router } from 'vue-router'

// The route we arrived from to reach the current page, or null on a direct entry
// (deep link / reload / new tab) where vue-router's START_LOCATION has no matched records.
let previousRoute: RouteLocationNormalized | null = null

export function recordNavigation(from: RouteLocationNormalized): void {
  previousRoute = from.matched.length > 0 ? from : null
}

export function useNavigationHistory() {
  function goBack(router: Router, fallback: RouteLocationRaw): void {
    if (previousRoute) router.back()
    else router.push(fallback)
  }

  return { goBack }
}
