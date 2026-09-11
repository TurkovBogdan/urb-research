import { ApiError } from './client/createClient'
import { i18n } from '@/plugins/i18n'

// Человеческий текст отказа. Бэкенд отдаёт машинный `code` плюс уже локализованный `error`;
// предпочитаем СВОЙ словарь (`common.errors.<code>`), чтобы формулировки жили рядом с остальным
// интерфейсом, и падаем на текст бэкенда для кодов, которых фронт не знает, затем на общий.
// Работает вне компонентов (сторы, клиент API) — читает глобальный инстанс i18n.
export function errorText(e: unknown): string {
  const t = i18n.global.t

  // `common.` — под этим пространством смонтирован общий словарь (`plugins/i18n.ts`);
  // голый `errors.*` промахнулся бы молча.
  if (e instanceof ApiError) {
    // Упёрлись в лимит. Ответ несёт `Retry-After`, и назвать секунды честнее, чем «попробуйте
    // позже»: человек иначе жмёт снова и снова, продлевая себе же окно.
    if (e.status === 429) {
      return e.retryAfter === undefined
        ? t('common.errors.throttled')
        : t('common.errors.throttled_wait', { seconds: e.retryAfter })
    }

    // Коды приходят и от бэкенда, и от самого клиента (`network`/`timeout`/`protocol`).
    if (e.code) {
      const key = `common.errors.${e.code}`
      const translated = t(key)
      if (translated !== key) return translated
    }

    return e.message || t('common.errors.generic')
  }

  return e instanceof Error && e.message ? e.message : t('common.errors.generic')
}
