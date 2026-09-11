<script setup lang="ts">
// Навигация по разделам длинной страницы: липкий столбец ссылок с подсветкой того раздела,
// который сейчас читают.
//
// Прокручивается не окно, а зона содержимого (`PageLayout` → `.page-layout__content`), поэтому
// и слушать, и мотать нужно её: `window.scrollY` тут всегда ноль, а `scrollIntoView` увёл бы
// вместе с зоной весь макет.
import {
  computed,
  onActivated,
  onBeforeUnmount,
  onMounted,
  ref,
  type ComponentPublicInstance,
} from 'vue'

export interface NavSection {
  /** `id` элемента раздела на странице. */
  id: string
  label: string
  /** Показывается рядом с подписью, как счётчик у заголовка раздела. */
  count?: number
  /** Вложенность: 0 (умолчание) — раздел страницы, 1 — заголовок внутри него. */
  depth?: number
}

const props = defineProps<{ sections: NavSection[] }>()

// Список — `TransitionGroup`, поэтому ссылка ведёт на компонент, а нужен его корневой узел.
const root = ref<ComponentPublicInstance | null>(null)
const listElement = computed(() => (root.value?.$el ?? null) as HTMLElement | null)
const activeId = ref('')

// Воздух над разделом, к которому перемотали: без него заголовок упирается в самую кромку и
// читается как обрезанный.
const SCROLL_OFFSET = 48

// Раздел считается текущим, как только его верх поднялся выше этой линии — не от самого края,
// иначе подсветка перескакивает уже на первом пикселе прокрутки. Линия ниже места, куда встаёт
// перемотка, поэтому доехавший раздел сразу же и подсвечивается.
const ACTIVE_LINE_OFFSET = SCROLL_OFFSET + 48

// Запас до низа, в пределах которого страница считается домотанной. Последний раздел часто
// короче экрана и по правилу линии не активировался бы вовсе.
const BOTTOM_EPSILON = 4

const scroller = computed(
  () => listElement.value?.closest('.page-layout__content') as HTMLElement | null,
)

function sectionElement(id: string): HTMLElement | null {
  return scroller.value?.querySelector(`#${CSS.escape(id)}`) ?? null
}

function syncActive() {
  const container = scroller.value
  if (!container || !props.sections.length) return

  const reachedBottom =
    container.scrollTop + container.clientHeight >= container.scrollHeight - BOTTOM_EPSILON
  if (reachedBottom) {
    activeId.value = props.sections[props.sections.length - 1].id
    return
  }

  const line = container.getBoundingClientRect().top + ACTIVE_LINE_OFFSET
  let current = props.sections[0].id
  for (const section of props.sections) {
    const element = sectionElement(section.id)
    if (element && element.getBoundingClientRect().top <= line) current = section.id
  }
  activeId.value = current
}

function goTo(id: string) {
  const container = scroller.value
  const element = sectionElement(id)
  if (!container || !element) return
  const offset = element.getBoundingClientRect().top - container.getBoundingClientRect().top
  container.scrollTo({
    top: Math.max(0, container.scrollTop + offset - SCROLL_OFFSET),
    behavior: 'smooth',
  })
}

function listen() {
  scroller.value?.addEventListener('scroll', syncActive, { passive: true })
  window.addEventListener('resize', syncActive)
}

function unlisten() {
  scroller.value?.removeEventListener('scroll', syncActive)
  window.removeEventListener('resize', syncActive)
}

onMounted(() => {
  listen()
  syncActive()
})

// KeepAlive держит страницу живой между визитами: слушатель снят не был, но позиция прокрутки
// восстанавливается уже после активации — пересчитываем.
onActivated(syncActive)
onBeforeUnmount(unlisten)
</script>

<template>
  <VCard variant="outlined" rounded="lg" tag="nav" class="section-nav">
    <!-- Список пунктов меняется дважды: под поиском (разделы уходят и возвращаются) и при переходе
         на другой артефакт — колонка живёт в общей рамке и переживает его. И там и там смена
         показывается движением: мгновенная подмена читается как подмена страницы под рукой. -->
    <TransitionGroup ref="root" tag="div" name="nav-item" class="section-nav__list">
      <button
        v-for="section in sections"
        :key="section.id"
        type="button"
        class="section-nav__link"
        :class="{
          'section-nav__link--active': section.id === activeId,
          'section-nav__link--nested': section.depth,
        }"
        @click="goTo(section.id)"
      >
        <span class="section-nav__label">{{ section.label }}</span>
        <span v-if="section.count !== undefined" class="section-nav__count">{{ section.count }}</span>
      </button>
    </TransitionGroup>
  </VCard>
</template>

<style scoped>
/* Плашка той же породы, что и карточки разделов (outlined + rounded lg приходят пропсами),
   поэтому оглавление читается как ещё один блок страницы, а не как набор голых ссылок. */
/* Высоту и липкость задаёт страница (компонент не знает, что стоит рядом с ним в колонке);
   здесь — только внутреннее устройство: список забирает остаток и прокручивается сам, если
   оглавление длинного документа выше отведённого места. */
.section-nav {
  padding: 6px;
  display: flex;
  min-height: 0;
}

.section-nav__list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
  flex: 1;
  overflow-y: auto;
}

/* Схлопывание пунктов опирается на `interpolate-size` (auto ↔ 0); где его нет, список меняется
   мгновенно, как и раньше. */
.section-nav__list {
  interpolate-size: allow-keywords;
}

/* Движение здесь служебное: кому оно мешает, тот отключил его в системе. */
@media (prefers-reduced-motion: reduce) {
  .nav-item-enter-active,
  .nav-item-leave-active,
  .nav-item-move {
    transition: none;
  }
}

/* Сброс оформления кнопки: элемент выбран за поведение (не переход, а прокрутка своей же
   страницы), а выглядеть должен ссылкой — без него браузер рисует серую плашку с рамкой. */
.section-nav__link {
  appearance: none;
  border: 0;
  font: inherit;
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  /* Слева шире: там живёт метка текущего раздела, и место под неё занято всегда — иначе
     подпись дёргалась бы вбок в момент подсветки. */
  padding: 7px 10px 7px 20px;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: 13px;
  line-height: 1.45;
  text-align: start;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.14s ease, background-color 0.14s ease;
}

/* Метка — отдельная закруглённая полоска ВНУТРИ пункта, а не его граница: граница обрезалась бы
   скруглением угла и читалась как брак. Она же растёт из точки в штрих при смене раздела, поэтому
   переход между пунктами виден движением, а не морганием. */
.section-nav__link::before {
  content: '';
  position: absolute;
  left: 9px;
  top: 50%;
  width: 2px;
  height: 3px;
  border-radius: 1px;
  background: var(--text-faint);
  transform: translateY(-50%);
  opacity: 0;
  transition: height 0.18s ease, opacity 0.14s ease, background-color 0.14s ease;
}

.section-nav__link:hover {
  color: var(--text);
  background: var(--surface-hi);
}

.section-nav__link:hover::before {
  opacity: 1;
}

.section-nav__link--active {
  color: var(--text);
  background: var(--accent-soft);
  font-weight: 500;
}

.section-nav__link--active::before {
  height: 15px;
  opacity: 1;
  background: var(--accent);
}

/* Вложенный пункт — заголовок внутри раздела: сдвинут под метку родителя и набран мельче,
   чтобы список читался деревом, а не сплошной лентой. Длинные заголовки обрезаются в одну
   строку: в узкой колонке перенос на три строки съедает всё оглавление. */
.section-nav__link--nested {
  padding-left: 32px;
  font-size: 12px;
  color: var(--text-faint);
}

.section-nav__link--nested .section-nav__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-nav__link--nested::before {
  left: 21px;
}

.section-nav__link--nested:hover {
  color: var(--text-muted);
}

.section-nav__link--nested.section-nav__link--active {
  color: var(--text);
}

.section-nav__label {
  min-width: 0;
  flex: 1;
}

.section-nav__count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  transition: color 0.14s ease;
}

.section-nav__link--active .section-nav__count {
  color: var(--text-muted);
}

/* Узкий экран: отдельного столбца под панель уже нет — она ложится над содержимым строкой
   ссылок. Липкость там вредна: закреплённая полоса съела бы и без того малую высоту. */
@media (max-width: 1099px) {
  .section-nav__list {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
  }

  /* В строку метка-штрих не нужна: пункты стоят рядом, и заливка сама показывает текущий. */
  .section-nav__link {
    padding-inline: 12px;
  }

  .section-nav__link::before {
    display: none;
  }
}

/* Приход и уход пунктов. Пункт не просто гаснет, а схлопывается по высоте — иначе плашка прыгала
   бы поверх аккуратно тающих строк. Правила стоят ПОСЛЕ `.section-nav__link`: у них одинаковый
   вес, и собственный `transition` пункта иначе перебивал бы этот.
   `min-height: 0` обязателен: у элемента колонки-флекса минимальная высота по умолчанию равна его
   содержимому, и до нуля он не сжался бы — схлопывание вставало бы на строке текста. */
.nav-item-enter-active,
.nav-item-leave-active {
  overflow: hidden;
  min-height: 0;
  transition:
    opacity 0.18s ease,
    transform 0.18s ease,
    height 0.18s ease,
    padding-top 0.18s ease,
    padding-bottom 0.18s ease;
}

.nav-item-move {
  transition: transform 0.18s ease;
}

.nav-item-enter-from,
.nav-item-leave-to {
  opacity: 0;
  height: 0;
  padding-top: 0;
  padding-bottom: 0;
  transform: translateY(-4px);
}

/* Движение здесь служебное: кому оно мешает, тот отключил его в системе. */
@media (prefers-reduced-motion: reduce) {
  .nav-item-enter-active,
  .nav-item-leave-active,
  .nav-item-move {
    transition: none;
  }
}
</style>
