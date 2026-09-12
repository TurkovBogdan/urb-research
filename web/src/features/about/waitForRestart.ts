/**
 * Ожидание перезапуска: сначала бэкенд должен пропасть, и только потом — ответить.
 *
 * Ждать одного «ответил» нельзя: между ответом на запуск и остановкой процессов проходят
 * секунды (`uv run`, опрос remote), и опрос попал бы в ещё живой СТАРЫЙ бэкенд — страница
 * перезагрузилась бы, чтобы через мгновение упасть вместе с ним.
 *
 * Клиент API здесь не годится: его отказы в это время — нормальный ход событий, а не ошибки,
 * которые стоит показывать. Отсюда голый `fetch`, тихо глотающий отказы.
 */

const HEALTH_URL = `${import.meta.env.VITE_API_BASE ?? ''}/internal/health`

const POLL_INTERVAL_MS = 2000
/** Сколько ждём исчезновения. Не дождались — значит команда отказалась, не тронув процессы. */
const DISAPPEARANCE_BUDGET_MS = 90 * 1000
/** Полная последовательность: остановка, sync, копия базы, миграции, старт. */
const RETURN_BUDGET_MS = 15 * 60 * 1000

export async function waitForRestart(): Promise<boolean> {
  const wentDown = await waitUntil(() => backendIsServing().then((up) => !up), DISAPPEARANCE_BUDGET_MS)
  if (!wentDown) return false

  return waitUntil(backendIsServing, RETURN_BUDGET_MS)
}

/** «Жив» — это `ok`: деградировавший бэкенд отвечает 200 и заглушкой, перезагружать рано. */
async function backendIsServing(): Promise<boolean> {
  try {
    const response = await fetch(HEALTH_URL, { cache: 'no-store' })
    if (!response.ok) return false
    const payload = (await response.json()) as { status?: string }
    return payload.status === 'ok'
  } catch {
    return false
  }
}

async function waitUntil(reached: () => Promise<boolean>, budgetMs: number): Promise<boolean> {
  const deadline = Date.now() + budgetMs
  while (Date.now() < deadline) {
    if (await reached()) return true
    await sleep(POLL_INTERVAL_MS)
  }
  return false
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
