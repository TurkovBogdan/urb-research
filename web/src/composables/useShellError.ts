import { readonly, ref } from 'vue'
import type { ErrorKind } from '@/constants/errors'

// Отказ, который шелл показывает ВМЕСТО содержимого маршрута, не трогая адресную строку: адрес
// остаётся тем, на который пришёл человек. Уход на отдельный `/403` стирал бы единственную улику
// — что именно открывали, — и вместе с ней ломал бы и обращение в поддержку, и аналитику.
//
// Ставят: клиент API (403 на чтение), перехватчик ошибок рендера, обработчик провала навигации.
// Снимает — любая следующая навигация (гвард в начале каждого перехода).
const kind = ref<ErrorKind | null>(null)

export const shellError = readonly(kind)

export function setShellError(next: ErrorKind): void {
  kind.value = next
}

export function clearShellError(): void {
  kind.value = null
}
