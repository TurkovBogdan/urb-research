<script setup lang="ts">
// Название артефакта на месте: `InlineEdit` плюс единственная доменная часть — когда правку
// считать законченной. Одна обёртка на исследование, область и заметку: у всех трёх это одно
// поле с одним смыслом, различаются они лишь тем, где название написано.
//
// Сохраняет не компонент: он отдаёт `save` наверх и закрывается, когда сверху приедет новое имя.
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import InlineEdit from '@/components/InlineEdit.vue'

/** Столько принимает бэкенд (`TitleBody`): длиннее не отправляем вовсе. */
const MAX_LENGTH = 128

const props = withDefaults(defineProps<{
  title: string
  /** Имя поля для скринридера: «Название исследования» / «…области» / «…заметки». */
  label: string
  /** Запрос в полёте: поле и кнопки заблокированы. */
  saving?: boolean
  /** `title` — название и есть шапка страницы (исследование); `field` — строка внутри карточки. */
  variant?: 'field' | 'title'
  /** Уровень в дереве доступности. Задают там, где название И ЕСТЬ заголовок страницы. */
  heading?: 1 | 2 | 3 | 4 | 5 | 6
}>(), {
  saving: false,
  variant: 'field',
  heading: undefined,
})

const emit = defineEmits<{ save: [string] }>()

const { t } = useI18n()

const editing = ref(false)
// Правку начали МЫ и ждём её итога. Без этого фоновое обновление страницы (имя сменил агент)
// выбрасывало бы набранный черновик.
const submitted = ref(false)

function save(title: string): void {
  submitted.value = true
  emit('save', title)
}

// Новое имя сверху при НАШЕЙ отправке = сохранение прошло. Отказ имени не меняет, поэтому поле
// остаётся открытым с набранным текстом.
watch(() => props.title, () => {
  if (!submitted.value) return

  submitted.value = false
  editing.value = false
})

watch(editing, (open) => {
  if (!open) submitted.value = false
})
</script>

<template>
  <InlineEdit
    v-model:editing="editing"
    :variant="variant"
    :heading="heading"
    editable
    :value="title"
    :label="label"
    :edit-label="t('research.action.rename')"
    :saving="saving"
    :maxlength="MAX_LENGTH"
    @save="save"
  />
</template>
