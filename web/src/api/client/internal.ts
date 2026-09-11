// Client for the INTERNAL API (zone `/internal/*`) — the single way the frontend talks to our
// own backend. Общая фабрика (`createClient`) плюс политика ЭТОЙ зоны; отдельный клиент под
// будущий внешний/публичный API заводится там же одной строкой. Вызывающие передают
// зона-относительные пути ('/settings/modules') — префикс принадлежит этому файлу.
import { createClient } from './createClient'
import { errorText } from '@/api/errorText'
import { setShellError } from '@/composables/useShellError'
import { pushToast } from '@/composables/useToasts'

export { ApiError } from './createClient'
export type { ApiErrorBody, RequestOptions } from './createClient'

export const internalApi = createClient({
  prefix: '/internal',
  origin: import.meta.env.VITE_API_BASE ?? '',
  // ⚠️ Авторизации у зоны сегодня нет: CSRF-проверки на бэкенде не существует, и включённый
  // тумблер добавил бы провальный GET `/internal/csrf-cookie` перед каждой записью. Здесь же
  // появится `loginPath`/`onUnauthenticated`, если вход когда-нибудь заведётся.
  csrf: false,
  // Отказ в правах — экран на текущем адресе, а не уход на отдельный.
  onForbidden: () => setShellError('forbidden'),
  // Отказ, который экран не показал сам, всплывает сообщением.
  onError: (error) => pushToast(errorText(error)),
})
