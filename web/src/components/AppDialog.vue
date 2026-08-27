<script setup lang="ts">
// Модальное окно портала целиком: карточка, шапка с крестиком, тело и полоса кнопок. Собирать
// `VDialog` + `VCard` вручную больше не нужно — так анатомия окна не может разойтись по экранам,
// а ловушки Vuetify (`VCardTitle`, `VCardActions`) не попадают в код вовсе.
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import DialogHeader from './DialogHeader.vue'
import DialogActions from './DialogActions.vue'

// Ширина — параметр окна, но не произвольный: три ступени по назначению вместо россыпи литералов.
const WIDTHS = {
  narrow: 440,  // подтверждение, короткий вопрос
  base: 560,    // форма, деталка
  wide: 900,    // две колонки, оплата
}

const open = defineModel<boolean>({ required: true })

const props = withDefaults(defineProps<{
  title: string
  description?: string
  size?: keyof typeof WIDTHS
  /** Не закрывается кликом мимо и по Esc: выход только крестиком и кнопками. */
  persistent?: boolean
  /** Линия под шапкой. Снимать у окна БЕЗ контентного блока (вопрос без содержимого). */
  rule?: boolean
  /** Идёт работа: крестик виден, но не работает. */
  closeDisabled?: boolean
  /** Тело до краёв карточки — для контента со своим фоном (колонки оплаты). */
  flush?: boolean
  /** Длинный контент: прокручивается тело, шапка и кнопки остаются на месте. */
  scrollable?: boolean
}>(), {
  description: undefined,
  size: 'base',
  persistent: false,
  rule: true,
  closeDisabled: false,
  flush: false,
  scrollable: false,
})

const slots = defineSlots<{
  default(): unknown
  actions?(): unknown
}>()

const maxWidth = computed(() => WIDTHS[props.size])

// Без кнопок тело само отвечает за нижний отступ карточки. Проверяем слот, а не `:last-child`:
// VCard подмешивает `.v-card__underlay` последним ребёнком и позиционный селектор промахивается.
const hasActions = computed(() => Boolean(slots.actions))

// ── Плавная смена высоты ──────────────────────────────────────────────────────────────────
// Содержимое меняется уже после открытия: догрузился платёжный виджет, переключили вкладку, форма
// сменилась на «отправлено». Скачок читается рывком — окно по центру, и уезжают обе кромки.
//
// Анимируем ОБЁРТКУ тела, а не карточку: карточку Vuetify делает flex-элементом с
// `flex: 1 1 var(--v-card-height, 100%)`, и свойство `height` на неё не действует вовсе.
// Обёртка получает явную высоту на время перехода и отпускается обратно в `auto`, чтобы
// содержимое снова управляло размером само.
const sizer = ref<HTMLElement | null>(null)
const content = ref<HTMLElement | null>(null)

let observer: ResizeObserver | null = null

// Высоту помним САМИ: наблюдатель приходит уже после раскладки, и обёртка к этому моменту равна
// новому содержимому — сравнивать её с ним бессмысленно, разницы там не увидеть.
let previous: number | null = null

function release(): void {
  const element = sizer.value
  if (element === null) return

  element.style.height = ''
  element.style.overflow = ''
}

function onContentResize(): void {
  const element = sizer.value
  if (element === null || content.value === null) return

  const next = content.value.offsetHeight
  if (previous === null || next === previous) {
    previous = next
    return
  }

  const from = previous
  previous = next

  // Прячем перелив только на время хода: в покое из окна могут торчать нужные вещи.
  element.style.overflow = 'hidden'
  element.style.height = `${from}px`
  void element.offsetHeight  // reflow: без него браузер склеит оба значения в одно
  element.style.height = `${next}px`
  element.addEventListener('transitionend', release, { once: true })
}

function stopWatching(): void {
  observer?.disconnect()
  observer = null
  previous = null
}

// Подписываемся на САМ элемент, а не на `open`: содержимое окна монтируется позже открытия, и в
// момент смены модели его ещё нет.
watch(content, (element) => {
  stopWatching()

  if (element === null) return

  // Плавность — украшение: при выключенной анимации в системе окно меняет высоту сразу.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

  observer = new ResizeObserver(onContentResize)
  observer.observe(element)
})

onBeforeUnmount(stopWatching)
</script>

<template>
  <VDialog
    v-model="open"
    :max-width="maxWidth"
    :persistent="persistent"
    :scrollable="scrollable"
  >
    <VCard>
      <DialogHeader
        :title="title"
        :description="description"
        :rule="rule"
        :close-disabled="closeDisabled"
        @close="open = false"
      />

      <div
        class="app-dialog__body"
        :class="{
          'app-dialog__body--flush': flush,
          'app-dialog__body--last': !hasActions,
          'app-dialog__body--tight': !rule,
          'app-dialog__body--scrollable': scrollable,
        }"
      >
        <div ref="sizer" class="app-dialog__sizer">
          <div ref="content">
            <slot />
          </div>
        </div>
      </div>

      <DialogActions v-if="hasActions">
        <slot name="actions" />
      </DialogActions>
    </VCard>
  </VDialog>
</template>

<style scoped>
/* Типографика повторяет прежний VCardText — тело окна набрано мельче страницы.
   Снизу половина зазора до кнопок, вторую половину приносит DialogActions. */
.app-dialog__body {
  padding: 16px 24px 12px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
}

/* Прокручивается САМО тело, а не вложенный блок: иначе полоса прокрутки встаёт по внутреннему
   краю отступов и висит в 24px от рамки карточки. Высоту ограничивает окно (`scrollable` у
   VDialog делает карточку колонкой), поэтому своей max-height тут нет. */
.app-dialog__body--scrollable {
  flex: 1 1 auto;
  overflow-y: auto;
}

/* Кнопок нет — низ карточки держит тело, и повторяет верх шапки. */
.app-dialog__body--last { padding-bottom: 22px; }

/* Линии нет — расстояние до текста задаёт одна шапка, иначе два отступа складываются. */
.app-dialog__body--tight { padding-top: 0; }

.app-dialog__body--flush { padding: 0; }

/* Явную высоту на время смены содержимого ставит скрипт; в покое здесь `auto`. */
.app-dialog__sizer { transition: height 220ms cubic-bezier(.4, 0, .2, 1); }
</style>
