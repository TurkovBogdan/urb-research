import { onActivated, watch } from 'vue'
import { useRoute } from 'vue-router'

/**
 * Загрузка деталки по коду из адреса — общая для всех пяти страниц объекта.
 *
 * Две причины перечитать: страницу открыли (`KeepAlive` держит ОДИН экземпляр на маршрут, поэтому
 * возврат на неё — это активация, а не монтирование) и код в адресе сменился, пока страница
 * открыта (переход с исследования на исследование по ссылке в тексте).
 *
 * Сверка маршрута обязательна: `KeepAlive` не размонтирует ушедшую вьюху, а параметр `code` у всех
 * деталок называется одинаково — без неё наблюдатель кэшированной страницы зоны срабатывал бы на
 * коде заметки и запрашивал зону по нему, получая 404 и записывая отказ в свой стор. Сверяемся с
 * ИМЕНЕМ маршрута, а не с флагом «страница на экране»: к моменту, когда наблюдатель уходящей вьюхи
 * срабатывает, адрес уже сменился, а её собственная деактивация ещё не наступила.
 */
export function useDetailReload(load: (code: string) => void): { reload: () => void } {
  const route = useRoute()
  let ownRoute: string | undefined

  function reload(): void {
    const code = route.params.code
    if (typeof code === 'string' && code) load(code)
  }

  onActivated(() => {
    ownRoute = String(route.name)
    reload()
  })

  watch(() => route.params.code, () => {
    if (String(route.name) === ownRoute) reload()
  })

  return { reload }
}
