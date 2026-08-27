<script setup lang="ts">
// Карточка полки: название, описание, иконка, позиция. Одно окно на создание и на правку —
// поля и проверки у них общие, а различие ровно в двух местах (заголовок и вызываемая ручка),
// и второй компонент ради них означал бы две формы, расходящиеся при первой же новой колонке.
// Режим задаёт проп: `group === null` — создание.
//
// Анатомия окна (шапка, тело, полоса кнопок) приходит из AppDialog, здесь только поля.
// Форма ведёт СВОЮ копию значений и синхронизируется при открытии: правка не должна менять
// карточку в списке до сохранения, а отмена обязана оставлять список нетронутым.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/components/AppDialog.vue'
import IconColorPicker from '@/components/IconColorPicker.vue'
import { errorText } from '@/api/errorText'

import { groupColorNames, groupColorVars } from '../constants/groupColors'
import { groupIcon, groupIconNames } from '../constants/groupIcons'
import { createGroup, updateGroup, type GroupBody, type GroupRow } from '../api'

// Стартовая позиция новой полки — та же, что ставит бэкенд (`GROUP_SORT_DEFAULT`). Показываем
// её числом, а не прячем в умолчание ручки: позиция участвует в сортировке, и человек должен
// видеть, куда встанет полка, ещё до сохранения.
const SORT_DEFAULT = 500

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ group: GroupRow | null }>()
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()

const icons = groupIconNames()
const colors = groupColorNames()

const title = ref('')
const description = ref('')
const icon = ref<string | null>(null)
const color = ref<string | null>(null)
const sort = ref(SORT_DEFAULT)
const saving = ref(false)
const error = ref<string | null>(null)

const creating = computed(() => props.group === null)

watch(() => [open.value, props.group] as const, ([isOpen, group]) => {
  if (!isOpen) return
  title.value = group?.title ?? ''
  description.value = group?.description ?? ''
  icon.value = group?.icon || null
  color.value = group?.color || null
  sort.value = group?.sort ?? SORT_DEFAULT
  error.value = null
}, { immediate: true })

async function save() {
  if (!title.value.trim()) return
  saving.value = true
  error.value = null
  const body: GroupBody = {
    title: title.value.trim(),
    description: description.value.trim(),
    icon: icon.value ?? '',
    color: color.value ?? '',
    sort: sort.value,
  }
  try {
    // `report: false` — отказ операции показываем ЗДЕСЬ, рядом с кнопкой: окно остаётся
    // открытым с введённым текстом, а тост увёл бы сообщение из поля зрения.
    await (props.group
      ? updateGroup(props.group.code, body, { report: false })
      : createGroup(body, { report: false }))
    open.value = false
    emit('saved')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppDialog
    v-model="open"
    :title="creating ? t('research.group.form.create_title') : t('research.group.form.title')"
    :description="props.group?.code"
    size="base"
    :persistent="saving"
    :close-disabled="saving"
  >
    <!-- Порядок: что это (название, описание) → где встанет (позиция) → как выглядит (иконка).
         Пикер последний — он самый высокий, и над ним ничего не должно прыгать при прокрутке. -->
    <div class="group-form">
      <VTextField
        v-model="title"
        :label="t('research.group.form.name')"
        variant="outlined"
        density="comfortable"
        :maxlength="128"
        hide-details
        autofocus
      />

      <VTextarea
        v-model="description"
        :label="t('research.group.form.description')"
        variant="outlined"
        density="comfortable"
        rows="2"
        auto-grow
        :maxlength="512"
        hide-details
      />

      <VNumberInput
        v-model="sort"
        :label="t('research.group.form.sort')"
        variant="outlined"
        density="comfortable"
        :min="0"
        :max="9999"
        :hint="t('research.group.form.sort_hint')"
        persistent-hint
      />

      <div class="group-form__field">
        <span class="group-form__label">{{ t('research.group.form.look') }}</span>
        <!-- Предпросмотр плашки живёт внутри панели, рядом с палитрой: рисунок и цвет
             оценивают вместе, врозь выбирать их не по чему.
             Высота — три ряда плюс краешек четвёртого: обрезанный ряд и есть признак того,
             что список прокручивается. Ровная высота выглядела бы как весь набор. -->
        <IconColorPicker
          v-model:icon="icon"
          v-model:color="color"
          :icons="icons"
          :colors="colors"
          :resolve-icon="groupIcon"
          :resolve-color="groupColorVars"
          :height="160"
          clearable
        />
      </div>

      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>
    </div>

    <template #actions>
      <VBtn variant="text" :disabled="saving" @click="open = false">
        {{ t('common.action.cancel') }}
      </VBtn>
      <VBtn
        color="primary"
        variant="flat"
        :loading="saving"
        :disabled="!title.trim()"
        @click="save"
      >
        {{ creating ? t('common.action.add') : t('common.action.save') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
/* Поля разделены одним шагом, а подсказка позиции живёт в своём поле (`persistent-hint`),
   поэтому дополнительного зазора под ним не нужно. */
.group-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Подпись прижата к своему полю теснее, чем поля друг к другу, — иначе она читается как
   заголовок всего блока, а не как метка пикера. */
.group-form__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}


.group-form__label {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
