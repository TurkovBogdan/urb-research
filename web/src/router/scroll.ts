import type { RouteLocationNormalized } from 'vue-router'

// Возврат по истории или новый переход — единственное, что роутер знает о прокрутке, и
// единственное, что нужно странице. Отличает их `savedPosition`: браузер отдаёт его роутеру
// только на back/forward, а на обычном переходе (клик по ссылке, `router.push`) там `null`.
//
// Сам роутер при этом не мотает ничего: прокручивается не окно, а зона содержимого
// (`PageLayout`), и позицию восстанавливает она — этот модуль отвечает лишь на вопрос «нас
// сюда вернули или мы сюда пришли».
let backNavigation = false

export function trackNavigationKind(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  savedPosition: { left: number; top: number } | null,
): false {
  backNavigation = savedPosition !== null
  return false
}

export function isBackNavigation(): boolean {
  return backNavigation
}
