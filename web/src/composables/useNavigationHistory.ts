import { computed, shallowRef, type ComputedRef } from 'vue'
import type { RouteLocationNormalized, RouteLocationRaw, Router } from 'vue-router'

// The route we arrived from to reach the current page, or null on a direct entry
// (deep link / reload / new tab) where vue-router's START_LOCATION has no matched records.
//
// Реактивная, потому что от неё зависит не только поведение кнопки, но и её подпись: возврат по
// истории ведёт «туда, откуда пришли», а запасной адрес — в конкретное место, и называется оно
// своим именем.
const previousRoute = shallowRef<RouteLocationNormalized | null>(null)

export function recordNavigation(from: RouteLocationNormalized): void {
  previousRoute.value = from.matched.length > 0 ? from : null
}

export function useNavigationHistory(): {
  goBack: (router: Router, fallback: RouteLocationRaw) => void
  hasHistory: ComputedRef<boolean>
} {
  function goBack(router: Router, fallback: RouteLocationRaw): void {
    if (previousRoute.value) router.back()
    else router.push(fallback)
  }

  /** Есть куда возвращаться по истории — значит, запасной адрес в этот раз не понадобится. */
  const hasHistory = computed(() => previousRoute.value !== null)

  return { goBack, hasHistory }
}
