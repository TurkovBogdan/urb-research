import type { Router } from 'vue-router'
import { setShellError } from '@/composables/useShellError'

// Выкладка уносит старые чанки Vite (хэш в имени), и у вкладки, открытой до неё, переход по
// ленивому маршруту падает МОЛЧА: навигация отменяется, экран остаётся прежним — «клик, и ничего».
// Правильный ответ тут не экран отказа, а перезагрузка на ТОТ ЖЕ адрес: свежий бандл покажет
// нужную страницу. Ключ в sessionStorage не даёт петли, если чанк не отдаётся и после перезагрузки.
const GUARD_KEY = 'app.chunk-reload'

// Текст ошибки динамического импорта различается по браузерам, общего типа у неё нет.
const CHUNK_ERROR = /dynamically imported module|Importing a module script failed|Failed to fetch/i

function reloadOnce(path: string): void {
  // Перезагрузка на этот адрес уже была и не помогла — дальше только честный экран сбоя.
  if (sessionStorage.getItem(GUARD_KEY) === path) {
    sessionStorage.removeItem(GUARD_KEY)
    setShellError('failure')

    return
  }

  sessionStorage.setItem(GUARD_KEY, path)
  window.location.assign(path)
}

export function setupChunkReload(router: Router): void {
  // Два входа в один и тот же сценарий: `vite:preloadError` ловит провал предзагрузки модуля
  // (в том числе вне навигации), `router.onError` — провал ленивого импорта самого маршрута.
  window.addEventListener('vite:preloadError', () => {
    reloadOnce(window.location.pathname + window.location.search + window.location.hash)
  })

  router.onError((error, to) => {
    if (!(error instanceof Error) || !CHUNK_ERROR.test(error.message)) return

    reloadOnce(to.fullPath)
  })

  // Дошли до места — предохранитель больше не нужен.
  router.afterEach(() => {
    sessionStorage.removeItem(GUARD_KEY)
  })
}
