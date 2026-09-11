<script setup lang="ts">
// Правка значения НА МЕСТЕ: в покое текст, по карандашу — поле на том же месте и той же метрике.
//
// Вход в правку не двигает вёрстку ни по одной оси. По вертикали за это отвечает единый токен
// `--ile-height`: высота одинакова в покое, в правке и без права правки, а текст в покое
// однострочный с многоточием (перенос сделал бы высоту зависимой от длины значения).
// По горизонтали — то, что и текст, и поле занимают ширину СВОЕГО СОДЕРЖИМОГО, а не всю
// свободную: поле открывается ровно той ширины, какой был текст, поэтому кнопка остаётся на
// месте карандаша. Отмена приходит справа от неё и растёт наружу, ничего не сдвигая.
import { computed, nextTick, ref, useSlots, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconCheck, IconLoader2, IconPencil, IconX } from '@tabler/icons-vue'

const props = withDefaults(defineProps<{
  /** Хранимое значение. Пустая строка = значения нет. */
  value: string
  /** Имя значения: подпись поля для скринридера. */
  label: string
  /** Подпись карандаша. По умолчанию — имя значения: у соседних строк подписи не совпадут. */
  editLabel?: string
  /** Что показать в покое, если это не сам `value` (страна: код в базе, имя на экране). */
  display?: string
  /** Текст на месте пустого значения. */
  empty?: string
  placeholder?: string
  editable?: boolean
  /** Запрос ИМЕННО этого значения в полёте: карандаш крутится, правка заперта. */
  saving?: boolean
  maxlength?: number
  /** `field` — строка реквизита, `title` — заголовок страницы. Отличаются только метрикой. */
  variant?: 'field' | 'title'
  /** Уровень заголовка в дереве доступности; без него текст остаётся простым `span`. */
  heading?: 1 | 2 | 3 | 4 | 5 | 6
  /** Пустое значение допустимо и означает «стереть». По умолчанию сохранение пустого запрещено. */
  allowEmpty?: boolean
}>(), {
  editLabel: undefined,
  display: undefined,
  empty: '',
  placeholder: undefined,
  editable: false,
  saving: false,
  maxlength: undefined,
  variant: 'field',
  heading: undefined,
  allowEmpty: false,
})

const emit = defineEmits<{ save: [string] }>()

/** Наружу — чтобы владелец закрыл правку сам: по приходу нового значения или по потере права. */
const editing = defineModel<boolean>('editing', { default: false })

const { t } = useI18n()
const slots = useSlots()

const draft = ref('')
const text = ref<HTMLElement | null>(null)
const action = ref<HTMLButtonElement | null>(null)
const field = ref<HTMLInputElement | null>(null)

const shown = computed(() => props.display ?? props.value)
const blank = computed(() => shown.value === '')
const draftBlank = computed(() => draft.value.trim() === '')

/** По чему меряется ширина поля: набранное, а на пустом — подсказка, чтобы её было видно целиком. */
const sizerText = computed(() => draft.value || props.placeholder || '')

/** Своим контролем (список стран) правку ведёт владелец: у неё нет «ввода», который подтверждают. */
const custom = computed(() => slots.control !== undefined)

async function start(): Promise<void> {
  if (!props.editable) return

  draft.value = props.value
  editing.value = true

  await nextTick()

  const input = field.value
  if (input === null) return

  input.focus()
  // Курсор в НАЧАЛО строки: `focus()` сам ставит его в конец, а значение чаще правят с начала.
  input.setSelectionRange(0, 0)
  // Прокрутку курсор за собой не тянет, когда значение шире поля: `focus()` уже увёл её в конец,
  // и человек видел бы хвост названия при курсоре в начале. Возвращаем руками.
  input.scrollLeft = 0
}

/** Закрыть правку и вернуть фокус на карандаш — иначе он улетает в `body`. */
function close(): void {
  editing.value = false
  draft.value = ''

  void nextTick(() => action.value?.focus())
}

function cancel(): void {
  if (!editing.value) return

  close()
}

function submit(): void {
  if (props.saving || (draftBlank.value && !props.allowEmpty)) return

  const next = draft.value.trim()

  // Ничего не изменилось — закрываемся молча, запрос ради того же значения не нужен.
  if (next === props.value) {
    close()
  } else {
    emit('save', next)
  }
}

// Право могло уйти под руками (перечитали карточку) — правку закрываем, иначе человек остаётся
// в поле без кнопок.
watch(() => props.editable, (allowed) => {
  if (!allowed) cancel()
})

defineExpose({ close })
</script>

<template>
  <span class="ile" :class="`ile--${variant}`">
    <!-- Свой контрол владельца (выпадающий список): держит ту же высоту строки, что и поле. -->
    <span v-if="editing && custom" class="ile__control">
      <slot name="control" :cancel="cancel" />
    </span>

    <!-- `data-value` — это и есть ширина поля: обёртка рисует ту же строку невидимой копией
         (см. стили), поле тянется за ней и растёт по мере ввода. -->
    <span
      v-else-if="editing"
      class="ile__text ile__grow"
      :data-value="sizerText"
    >
      <!-- `size="1"` — не размер поля на экране, а отказ от собственной ширины: по умолчанию input
           просит места на ~20 знаков, и на названии короче этого ширину диктовал бы он, а не текст. -->
      <input
        ref="field"
        v-model="draft"
        class="ile__input"
        type="text"
        size="1"
        :maxlength="maxlength"
        :placeholder="placeholder"
        :disabled="saving"
        :aria-label="label"
        @keydown.enter.prevent="submit"
        @keydown.esc.prevent="cancel"
      />
    </span>

    <span
      v-else
      ref="text"
      class="ile__text ile__value"
      :class="{ 'ile__value--blank': blank }"
      :role="heading ? 'heading' : undefined"
      :aria-level="heading"
      :title="shown || undefined"
      @dblclick="start()"
    >{{ blank ? empty : shown }}</span>

    <template v-if="editable">
      <!-- Своему контролу подтверждение не нужно: он сохраняет по выбору, у него нет ввода. -->
      <button
        v-if="!(editing && custom)"
        ref="action"
        type="button"
        class="ile__btn"
        :class="{ 'ile__btn--framed': editing, 'ile__btn--busy': saving }"
        :disabled="saving || (editing && draftBlank && !allowEmpty)"
        :title="editing ? t('common.action.save') : (editLabel ?? label)"
        :aria-label="editing ? t('common.action.save') : (editLabel ?? label)"
        @click="editing ? submit() : start()"
      >
        <IconLoader2 v-if="saving" :size="16" class="icon-spin" />
        <IconCheck v-else-if="editing" :size="16" />
        <IconPencil v-else :size="16" />
      </button>

      <!-- Отмена не просто проявляется, а раздвигает себе место: с одной прозрачностью соседняя
           галочка прыгала бы на ширину кнопки в первый же кадр. -->
      <Transition name="ile-btn">
        <button
          v-if="editing"
          type="button"
          class="ile__btn ile__btn--framed"
          :disabled="saving"
          :title="t('common.action.cancel')"
          :aria-label="t('common.action.cancel')"
          @click="cancel"
        >
          <IconX :size="16" />
        </button>
      </Transition>
    </template>
  </span>
</template>

<style scoped>
/* Высота строки — единственный размер, который здесь фиксируется жёстко: на нём держится
   обещание «правка не двигает вёрстку». Кнопка ровно этой высоты, текст и поле — тоже. */
.ile {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  height: var(--ile-height);

  /* Место под каретку за последним символом. Его несут ОБА состояния: поле — чтобы каретка в конце
     строки не липла к своему краю, текст в покое — чтобы поле открывалось ровно его ширины, а не
     на эти пиксели шире. */
  --ile-caret: 2px;
}

.ile--field {
  --ile-height: 28px;
  --ile-size: 15px;
  --ile-weight: 600;
}

/* Заголовок страницы: кегль и вес общие с `SectionHeader --l1` (18px / 600), высота — его же
   строка (18 × 1.3, округлённое вверх). Метрика продублирована, а не взята токеном: у
   `SectionHeader` её задаёт правило по классу, отдать наружу нечего. */
.ile--title {
  --ile-height: 24px;
  --ile-size: 18px;
  --ile-weight: 600;
}

/* Метрику держат ОБА состояния, и текст, и поле: разъехавшись, они дадут прыжок при нажатии. */
.ile__text {
  min-width: 0;
  font-size: var(--ile-size);
  font-weight: var(--ile-weight);
  line-height: 1.3;
  color: var(--text);
}
.ile--title .ile__text { letter-spacing: -0.02em; }

/* Однострочно и с многоточием: перенос на вторую строку сделал бы высоту зависимой от длины
   значения, а в правке она всё равно вернулась бы к одной строке — то есть дал бы прыжок.

   Ширина — по буквам (`flex: 0 1 auto`, как у обёртки поля ниже), а не вся свободная: карандаш
   стоит вплотную к тексту, и поле открывается ровно на его месте. Свободную строку значение
   занимать не должно ещё и потому, что тогда «расширяться при вводе» было бы некуда. */
.ile__value {
  flex: 0 1 auto;
  padding-right: var(--ile-caret);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.ile__value--blank { color: var(--text-muted); font-weight: 400; }

/* Поле ширины собственного текста, без единого замера в JS: обёртка — грид в одну клетку, куда
   положены и поле, и невидимая копия набранного (`::after` с `attr(data-value)`). Клетку
   распирает копия — поле тянется за ней, поэтому ширина едет следом за вводом.

   `min-width: 0` у клетки обязателен: без него она не сожмётся ниже длины строки, и на длинном
   значении поле вылезло бы поверх кнопок вместо того, чтобы упереться в край и прокручиваться
   внутри себя. Пол стёртого до конца значения держит `size="1"` у самого поля. */
.ile__grow {
  display: inline-grid;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 100%;
  padding-right: var(--ile-caret);
}
.ile__grow::after,
.ile__input {
  grid-area: 1 / 1;
  min-width: 0;
  width: auto;
}

/* `pre` — чтобы копия мерила пробелы так же, как их покажет поле, иначе набранное с двойным
   пробелом мерилось бы короче, чем выглядит. */
.ile__grow::after {
  content: attr(data-value);
  visibility: hidden;
  white-space: pre;
}

/* Поле бесцветное: ни фона, ни рамки, ни собственных отступов — на экране остаётся только текст,
   а режим правки называют кнопки справа. Метрику берём целиком от обёртки (`font: inherit`), иначе
   копия и поле мерили бы разные шрифты и ширина разъехалась бы. */
.ile__input {
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  letter-spacing: inherit;
  appearance: none;
}
.ile__input:focus { outline: none; }
.ile__input:disabled { color: var(--text-muted); }

/* Чужой контрол вписывается в ту же высоту: Vuetify иначе принесёт свою (40px у `compact`). */
.ile__control { flex: 1 1 auto; min-width: 0; }
.ile__control :deep(.v-field) { min-height: var(--ile-height); }
.ile__control :deep(.v-field__input) { min-height: var(--ile-height); padding-top: 0; padding-bottom: 0; }

/* Кнопки свои, а не `VBtn`: у того своя высота и плотность, из-за которых строка становится выше
   в режиме правки — ровно то, что этот компонент обязан не допускать.

   Стоят вплотную к значению, а не у правого края строки: у края они разъезжались бы с текстом на
   всю ширину пустоты, и глазу пришлось бы возвращаться от карандаша к названию. */
.ile__btn {
  flex: 0 0 auto;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--ile-height);
  height: var(--ile-height);
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
.ile__btn:hover:not(:disabled) { background: var(--surface-hi); color: var(--text); }
.ile__btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.ile__btn:disabled { cursor: default; opacity: 0.5; }

/* В правке кнопки перестают быть призраками: заливка на шаг темнее полотна (`--surface-hi` против
   `--bg`) плюс волосяная рамка. Рамка объявлена прозрачной ВЫШЕ, а не добавляется здесь: иначе
   кнопка вырастала бы на 2px в момент перехода в правку. */
.ile__btn--framed {
  background: var(--surface-hi);
  border-color: var(--border-soft);
  color: var(--text-muted);
}
.ile__btn--framed:hover:not(:disabled) { background: var(--surface-sunken); color: var(--text); }

/* Занятая кнопка не «погашенная»: запрос идёт, и вертушку видно в полную силу. */
.ile__btn--busy { opacity: 1; color: var(--text-muted); }

.ile-btn-enter-active,
.ile-btn-leave-active {
  overflow: hidden;
  transition: opacity 160ms ease, width 220ms ease, margin-left 220ms ease;
}
.ile-btn-enter-from,
.ile-btn-leave-to {
  width: 0;
  margin-left: -6px;
  opacity: 0;
}
</style>
