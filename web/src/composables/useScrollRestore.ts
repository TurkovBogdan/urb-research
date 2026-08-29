// Возврат позиции чтения одним присваиванием не делается: страница, на которую вернулись,
// собирается не мгновенно. Замер на деталке исследования (возврат с зоны): в момент активации
// её высота 1145px — данные ещё едут, — через 180мс 5884, ещё через 180 — 7452. Присвоенная
// сразу позиция сперва упирается в потолок короткой страницы, а потом её сдвигает сам браузер:
// дорисовка выше окна включает привязку прокрутки (`overflow-anchor`), и 900 превращались
// в 2469 — ровно на высоту приехавшего куска.
//
// Поэтому цель не ставится, а УДЕРЖИВАЕТСЯ, пока страница до неё дорастает. Отпускаем по трём
// поводам: цель достигнута и держится, вышло время, либо человек тронул прокрутку сам — его
// намерение старше нашего.
const HOLD_WINDOW_MS = 1200

// Чем человек забирает прокрутку себе. Отпустить рано нельзя: страница дорастает кусками, и
// между ними позиция бывает верной случайно — держим всё окно, а не «пока не совпало».
// `pointerdown` тут не про прокрутку, а про любое касание страницы: клик по оглавлению — тоже
// перемотка, и спорить с ней мы не вправе.
const USER_TAKEOVER_EVENTS = ['wheel', 'pointerdown'] as const

export function restoreScrollTop(element: HTMLElement, target: number): void {
  element.scrollTop = target
  if (target <= 0) return

  const deadline = performance.now() + HOLD_WINDOW_MS
  let released = false

  const release = () => {
    if (released) return
    released = true
    for (const event of USER_TAKEOVER_EVENTS) element.removeEventListener(event, release)
    window.removeEventListener('keydown', release)
  }

  for (const event of USER_TAKEOVER_EVENTS) element.addEventListener(event, release, { passive: true })
  window.addEventListener('keydown', release)

  const hold = () => {
    if (released) return
    if (performance.now() > deadline) return release()

    if (element.scrollTop !== target) element.scrollTop = target
    requestAnimationFrame(hold)
  }

  requestAnimationFrame(hold)
}
