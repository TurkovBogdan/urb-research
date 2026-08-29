<script setup lang="ts">
// Правка АБЗАЦА на месте — многострочный родственник `InlineEdit`. Разница ровно одна: там
// значение в одну строку и правится полем ввода, здесь текст в несколько строк и поля не видно
// вовсе. В покое это абзац; в правке — тот же абзац, только редактируемый: та же гарнитура,
// кегль, интерлиньяж и ширина, ни рамки, ни подложки, ни собственного размера.
//
// Обещание то же, что у `InlineEdit`: вход в правку не двигает вёрстку. У абзаца для этого нет
// фиксированной высоты, поэтому поле меряет само себя (`scrollHeight`) на открытии и на каждый
// ввод. Невидимая копия текста в CSS выглядела бы дешевле, но переносит строки не так, как их
// переносит поле: замер на живом описании давал 238px против 208px у того же абзаца.
//
// Сохраняет не компонент: он отдаёт `save` наверх и ждёт, пока владелец закроет правку.
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconCheck, IconLoader2, IconPencil, IconX } from '@tabler/icons-vue'

const props = withDefaults(defineProps<{
  /** Хранимое значение. Пустая строка = значения нет. */
  value: string
  /** Имя значения: подпись поля для скринридера. */
  label: string
  /** Текст на месте пустого значения. */
  empty?: string
  /** Запрос ИМЕННО этого значения в полёте: правка заперта, кнопки не отвечают. */
  saving?: boolean
  maxlength?: number
  /** Пустое значение допустимо и означает «стереть». */
  allowEmpty?: boolean
}>(), {
  empty: '',
  saving: false,
  maxlength: undefined,
  allowEmpty: false,
})

const emit = defineEmits<{ save: [string] }>()

/** Наружу — правку открывает владелец (ссылка «Изменить» рядом) и он же закрывает её по ответу. */
const editing = defineModel<boolean>('editing', { default: false })

const { t } = useI18n()

const draft = ref('')
const field = ref<HTMLTextAreaElement | null>(null)

const blank = computed(() => props.value === '')
const draftBlank = computed(() => draft.value.trim() === '')

/** Высота поля = высота его текста: `auto` сбрасывает прежнюю, иначе `scrollHeight` не уменьшается. */
function fitHeight(): void {
  const input = field.value
  if (input === null) return

  input.style.height = 'auto'
  input.style.height = `${input.scrollHeight}px`
}

// Черновик набирается с текущего значения, а курсор ставится в начало: `focus()` сам уводит его
// в конец, а текст чаще правят с начала.
watch(editing, async (open) => {
  if (!open) {
    draft.value = ''
    return
  }

  draft.value = props.value
  await nextTick()
  fitHeight()
  field.value?.focus()
  field.value?.setSelectionRange(0, 0)
})

function cancel(): void {
  editing.value = false
}

function submit(): void {
  if (props.saving || (draftBlank.value && !props.allowEmpty)) return

  const next = draft.value.trim()

  // Ничего не изменилось — закрываемся молча, запрос ради того же текста не нужен.
  if (next === props.value) cancel()
  else emit('save', next)
}
</script>

<template>
  <div class="ieb">
    <textarea
      v-if="editing"
      ref="field"
      v-model="draft"
      class="ieb__field"
      rows="1"
      :maxlength="maxlength"
      :disabled="saving"
      :aria-label="label"
      @input="fitHeight"
      @keydown.esc.prevent="cancel"
      @keydown.enter.ctrl.prevent="submit"
      @keydown.enter.meta.prevent="submit"
    />

    <p
      v-else
      class="ieb__value"
      :class="{ 'ieb__value--blank': blank }"
      @dblclick="editing = true"
    >{{ blank ? empty : value }}</p>

    <!-- Одна и та же строка в обоих состояниях: слева действия над текстом, справа то, что о нём
         сообщает владелец (дата обновления). Она не появляется и не исчезает, а только меняет
         левую половину, поэтому вход в правку не двигает карточку. Действия набраны `link-action`
         (общий класс в main.scss): это продолжение текста, а не панель управления им. -->
    <div class="ieb__row">
      <div class="ieb__actions">
        <template v-if="editing">
          <button
            type="button"
            class="link-action"
            :disabled="saving || (draftBlank && !allowEmpty)"
            @click="submit"
          >
            <IconLoader2 v-if="saving" :size="14" :stroke-width="1.8" class="icon-spin" />
            <IconCheck v-else :size="14" :stroke-width="1.8" />
            {{ t('common.action.save') }}
          </button>

          <button type="button" class="link-action" :disabled="saving" @click="cancel">
            <IconX :size="14" :stroke-width="1.8" />
            {{ t('common.action.cancel') }}
          </button>
        </template>

        <button v-else type="button" class="link-action" @click="editing = true">
          <IconPencil :size="14" :stroke-width="1.8" />
          {{ t('common.action.edit') }}
        </button>
      </div>

      <slot name="aside" />
    </div>
  </div>
</template>

<style scoped>
/* Метрику текста задаёт МЕСТО, куда компонент поставлен (класс на корне): гарнитура, кегль,
   интерлиньяж и предел строки приходят снаружи, а всё внутри их наследует — поэтому покой и
   правка выглядят одинаково по определению, а не по совпадению настроек. */
.ieb {
  display: block;
}

/* Метрика забирается у корня ЯВНО: правило для голого `p` в `main.scss` лежит вне слоёв, и
   наследованием его не перебить — абзац молча уезжал на свой интерлиньяж (20.8 против 23.8),
   то есть в покое текст стоял иначе, чем в правке. */
.ieb__value {
  margin: 0;
  font: inherit;
  line-height: inherit;
  letter-spacing: inherit;
  color: inherit;
  white-space: pre-wrap;
  cursor: text;
}

.ieb__value--blank {
  color: var(--text-faint);
}

/* Поля не видно: ни рамки, ни подложки, ни собственной метрики — на экране остаётся текст,
   в который поставили курсор. Высоту ставит скрипт, поэтому своя прокрутка полю не нужна. */
.ieb__field {
  display: block;
  width: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  line-height: inherit;
  letter-spacing: inherit;
  /* Форменным элементам браузер сбрасывает начертание в `auto`, а вокруг текст набран
     `optimizeLegibility` — с лигатурами и кернингом. Без этой строки правка отличалась бы от
     покоя формой букв: единственное расхождение, которое осталось после сверки всех
     вычисленных свойств. */
  text-rendering: inherit;
  resize: none;
  overflow: hidden;
  outline: none;
}

/* Действия слева, сведения владельца справа — по краям, а не в ряд: одно тут действие над
   текстом, другое сообщение о нём. */
.ieb__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}

.ieb__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
