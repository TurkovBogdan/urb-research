import type { RouteRecordNormalized, Router } from 'vue-router'

// Компонент маршрута — ленивый `import()`, и скачивается он ВНУТРИ навигации: пока чанк в пути,
// старая страница стоит неподвижно, а полоса прогресса с порогом 140 мс появиться не успевает
// (замер первого захода в деталку исследования — 107 мс, второго — 26 мс). Клик выглядит как
// «ничего не произошло», и только потом всё разом оживает.
//
// Лечится тем, что чанк приезжает до клика. Два входа: наведение или фокус на внутренней ссылке
// (курсор доходит до цели раньше нажатия) и разогрев на простое — до строк таблиц и карточек,
// которые ссылками не являются, наведение не дотягивается.
//
// Витрина дизайн-системы из разогрева исключена: сорок семь страниц, на рабочем пути не лежат,
// и по наведению каждая приедет сама.
const SHOWCASE_PREFIX = '/design-system'

// Помним ЗАПИСЬ маршрута, а не адрес: у деталки на каждый код свой адрес, но чанк один.
const warmed = new WeakSet<RouteRecordNormalized>()

function warm(record: RouteRecordNormalized): void {
  if (warmed.has(record)) return
  warmed.add(record)
  for (const component of Object.values(record.components ?? {})) {
    // Ленивый компонент — функция-загрузчик; уже разрешённый маршрут отдаёт сам объект.
    // Отказ глотаем: это упреждение, а не запрос, и настоящую ошибку покажет сама навигация.
    if (typeof component === 'function') void (component as () => Promise<unknown>)().catch(() => {})
  }
}

function warmPath(router: Router, path: string): void {
  for (const record of router.resolve(path).matched) warm(record)
}

function internalHref(target: EventTarget | null): string | null {
  const anchor = (target as Element | null)?.closest?.('a[href]')
  const href = anchor?.getAttribute('href') ?? ''
  return href.startsWith('/') ? href : null
}

function whenIdle(task: () => void): void {
  const idle = (window as { requestIdleCallback?: (cb: () => void, opts?: { timeout: number }) => void })
    .requestIdleCallback
  if (idle) idle(task, { timeout: 3000 })
  else setTimeout(task, 1000)
}

export function setupRoutePrefetch(router: Router): void {
  const probe = (event: Event) => {
    const href = internalHref(event.target)
    if (href) warmPath(router, href)
  }

  document.addEventListener('pointerover', probe, { passive: true })
  document.addEventListener('focusin', probe)

  whenIdle(() => {
    for (const record of router.getRoutes()) {
      if (!record.path.startsWith(SHOWCASE_PREFIX)) warm(record)
    }
  })
}
