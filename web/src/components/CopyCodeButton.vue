<script setup lang="ts">
// «Забрать код объекта» — одна кнопка на все шапки: и на деталках (`DetailHead`), и на страницах,
// чья шапка страничная (`PageHeader` у полки). Раньше разметка жила в `DetailHead`, и полка
// повторила бы её слово в слово — а расходятся такие копии молча, по одной правке за раз.
//
// Подпись обязательна: значок копирования сам по себе не говорит, ЧТО копируется, а рядом с именем
// объекта ответ должен читаться, а не угадываться.
import { useI18n } from 'vue-i18n'
import { IconCheck, IconCopy } from '@tabler/icons-vue'

import { useClipboard } from '@/composables/useClipboard'

defineProps<{ code: string }>()

const { t } = useI18n()
const { copy, isCopied } = useClipboard()
</script>

<template>
  <!-- Ответ об успехе даёт только значок: подпись говорит, что кнопка делает, и меняться от
       нажатия ей незачем — иначе кнопка на мгновение перестаёт быть той же самой, а вместе с
       длиной подписи дёргается и весь ряд. -->
  <VBtn variant="text" @click="copy(code)">
    <template #prepend>
      <IconCheck v-if="isCopied(code)" :size="16" class="copy-code__done" />
      <IconCopy v-else :size="16" />
    </template>
    {{ t('common.action.copy_code') }}
  </VBtn>
</template>

<style scoped>
/* Об успехе говорит сама смена значка, и цветом его называть незачем: копирование кода — рядовое
   действие, которое делают по многу раз, а зелёная вспышка в шапке читается как событие. Серый
   держит галочку в том же весе, что и значок, который она подменила. */
.copy-code__done {
  color: var(--text-muted);
}
</style>
