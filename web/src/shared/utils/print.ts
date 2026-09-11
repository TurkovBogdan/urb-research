// Печать документа на виртуальном принтере — то же самое, что «сохранить в PDF» в диалоге печати
// браузера.
//
// Печатается не тот экран, с которого нажали, а отдельный адрес печати того же приложения: вокруг
// документа на странице стоят колонка навигации, шапка и карточки разделов, и прятать их правилами
// `@media print` пришлось бы заново при каждом новом блоке. Скрытый кадр открывает страницу печати,
// где документ нарисован один на пустом листе, и печатает её: `print()`, вызванный у окна кадра,
// отправляет на принтер документ КАДРА, а не хозяина страницы.

const PRINT_SIGNAL = 'app-print'

interface PrintSignalMessage {
  signal: typeof PRINT_SIGNAL
  /** Пусто — документ готов к печати; иначе текст отказа, из-за которого печатать нечего. */
  error: string
}

// Лист A4 при 96 dpi. Размер кадра — не украшение невидимого элемента: раскладку схем и таблиц
// считают по ширине контейнера, и в кадре нулевой ширины она посчиталась бы под лист, которого
// не бывает.
const FRAME_WIDTH_PX = 794
const FRAME_HEIGHT_PX = 1123

// Сколько ждём сигнала готовности: страница печати успевает дозапросить исследование, разобрать
// тело, нарисовать схемы и дождаться шрифтов.
const READY_TIMEOUT_MS = 60_000

// Часть браузеров возвращает управление из `print()`, не дожидаясь конца печати. Снятый сразу
// кадр унёс бы с собой печатаемый документ, поэтому он живёт ещё немного после отправки.
const FRAME_KEEP_MS = 2000

function postSignal(error: string): void {
  const message: PrintSignalMessage = { signal: PRINT_SIGNAL, error }
  window.parent.postMessage(message, window.location.origin)
}

/** Зовёт страница печати, когда её документ нарисован целиком и его можно отправлять на принтер. */
export function announcePrintReady(): void {
  postSignal('')
}

/** Зовёт страница печати, когда документа не будет: печатать нечего, и ждать его — тоже. */
export function announcePrintFailure(error: string): void {
  postSignal(error)
}

/**
 * Напечатать страницу приложения по её адресу.
 *
 * Разрешается, когда документ ушёл на принтер; отклоняется с текстом отказа страницы печати —
 * либо с пустым, когда она не ответила вовсе (тогда причину знает только она сама).
 */
export function printPage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const frame = document.createElement('iframe')
    frame.setAttribute('aria-hidden', 'true')
    frame.src = url
    frame.style.cssText =
      `position:fixed;left:-10000px;top:0;border:0;width:${FRAME_WIDTH_PX}px;height:${FRAME_HEIGHT_PX}px;`

    const readyTimer = setTimeout(() => finish(new Error('')), READY_TIMEOUT_MS)

    function finish(failure: Error | null): void {
      clearTimeout(readyTimer)
      window.removeEventListener('message', onSignal)
      if (failure) {
        frame.remove()
        reject(failure)
        return
      }
      setTimeout(() => frame.remove(), FRAME_KEEP_MS)
      resolve()
    }

    function onSignal(event: MessageEvent): void {
      const message = event.data as PrintSignalMessage | undefined
      if (event.source !== frame.contentWindow || event.origin !== window.location.origin) return
      if (message?.signal !== PRINT_SIGNAL) return

      if (message.error) {
        finish(new Error(message.error))
        return
      }

      // Фокус в кадре обязателен: браузер печатает документ активного окна, и без него на принтер
      // ушла бы страница-хозяин со всем интерфейсом.
      frame.contentWindow?.focus()
      frame.contentWindow?.print()
      finish(null)
    }

    window.addEventListener('message', onSignal)
    document.body.appendChild(frame)
  })
}
