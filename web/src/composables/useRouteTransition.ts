import { readonly, ref, watch, type Ref } from 'vue'

// Переход между страницами идёт по часам CSS, а не по кадрам: пока главный поток занят, анимация
// не откладывается, а прокручивается вхолостую. Замер на деталке исследования — въезд длиной
// 150 мс, съеденный 88-миллисекундным первым рендером тела: непрозрачность прошла 0 → 0.05 → 0.99
// за 22 мс, то есть страница не проявилась, а щёлкнула. Поэтому тяжёлое содержимое ждёт конца
// перехода — так рывок превращается в лишнюю строку загрузки, которой не жалко.
//
// Флаг поднимает гвард роутера: он срабатывает раньше, чем смонтируется новая вьюха, а хук
// `before-enter` самого перехода — уже позже, и вьюха успела бы решить, что анимации нет.
// Снимает — сам `<Transition>` в App.vue по окончании въезда.
const busy = ref(false)

export const routeTransitionBusy = readonly(busy)

export function beginRouteTransition(): void {
  busy.value = true
}

export function endRouteTransition(): void {
  busy.value = false
}

/**
 * Можно ли рисовать тяжёлое: `true`, если переход не идёт, иначе — как только он закончится.
 *
 * Обратно в `false` не возвращается никогда: вьюхи живут в `KeepAlive`, и при следующем визите
 * их содержимое уже нарисовано — прятать готовую картинку на время анимации значило бы менять
 * один рывок на другой.
 */
export function useAfterRouteTransition(): Readonly<Ref<boolean>> {
  const ready = ref(!busy.value)

  if (!ready.value) {
    const stop = watch(busy, (running) => {
      if (running) return
      ready.value = true
      stop()
    })
  }

  return readonly(ready)
}
