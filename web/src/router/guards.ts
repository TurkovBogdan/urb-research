import type { RouteLocationNormalized, Router } from 'vue-router'
import { startNavigationProgress, stopNavigationProgress } from './progress'
import { dismissHoverTooltips } from './overlays'
import { recordNavigation } from '@/composables/useNavigationHistory'
import { beginRouteTransition, endRouteTransition } from '@/composables/useRouteTransition'
import { clearShellError } from '@/composables/useShellError'
import { i18n } from '@/plugins/i18n'

const APP_NAME = 'Uroboros.Research'

// Заголовок вкладки — часть навигации, а не украшение: смена маршрута его не меняет сама,
// скринридер читает его первым, а вкладок у ресёрча открывают много. Маршрут без `meta.title`
// оставляет одно имя приложения, а не выдуманную строку.
function applyDocumentTitle(to: RouteLocationNormalized): void {
  const key = to.meta.title
  document.title = key ? `${i18n.global.t(key)} — ${APP_NAME}` : APP_NAME
}

// После перехода фокус остаётся на ссылке, по которой кликнули: для клавиатуры и скринридера
// «ничего не произошло» становится буквальным. Переносим его в зону содержимого.
function focusContent(): void {
  const main = document.querySelector<HTMLElement>('.main-content')
  if (!main) return

  main.setAttribute('tabindex', '-1')
  main.focus({ preventScroll: true })
}

export function setupGuards(router: Router): void {
  router.beforeEach(() => {
    // Close any hover tooltip before KeepAlive deactivates its page and orphans the
    // teleported overlay (the activator's mouseleave never fires on a navigating click).
    dismissHoverTooltips()

    // Экран отказа принадлежит адресу, на котором его показали: уходим с адреса — снимаем.
    clearShellError()

    // Раньше, чем смонтируется новая вьюха: она обязана увидеть переход уже начатым, иначе
    // отложит своё тяжёлое содержимое не на анимацию, а в никуда. Снимает флаг сам переход.
    beginRouteTransition()

    // Arm the content-zone loading bar; the show-delay swallows instant swaps.
    startNavigationProgress()
    return true
  })

  // Destination resolved (incl. lazy chunk loaded) — drop the bar.
  router.afterEach((to, from, failure) => {
    recordNavigation(from)
    stopNavigationProgress()
    applyDocumentTitle(to)
    focusContent()
    // Сорвавшийся переход (повторная навигация на тот же адрес, отмена) до анимации не доходит,
    // и снять флаг будет некому — страница осталась прежней, а ждать её въезда уже нечего.
    if (failure) endRouteTransition()
  })
  // Aborted/failed navigation never reaches afterEach — clear the bar here too.
  router.onError(() => stopNavigationProgress())
}
