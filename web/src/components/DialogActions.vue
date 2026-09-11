<script setup lang="ts">
// Полоса кнопок модального окна. Отдельный компонент, а не `VCardActions`: тот раздаёт всем
// вложенным кнопкам `slim: true` и `variant: 'text'` через provideDefaults, из-за чего главное
// действие теряет заливку и высоту, а `color` перестаёт работать. Здесь кнопки обычные.
</script>

<template>
  <div class="dlg-actions">
    <slot />
  </div>
</template>

<style scoped>
/* Низ повторяет верх шапки, бока — общие 24px окна. Сверху минимум 12px: контент со своей
   прокруткой обрезается по краю, и без него кнопки упирались бы в срезанный текст. */
.dlg-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 24px 22px;
}
</style>
