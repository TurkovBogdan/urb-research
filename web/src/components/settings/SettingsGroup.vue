<script setup lang="ts">
// Карточка группы настроек: заголовок, пояснение под ним, дальше поля.
//
// Анатомия та же, что у карточки модуля на /settings/modules (заголовок → описание → линейка →
// поля с одинаковым шагом): группы настроек читаются одинаково независимо от того, лежит их
// значение в базе или в этом браузере. Описание тут — обычная строка, а не markdown: у клиентских
// настроек текст свой, а не пришедший из схемы бэкенда, и ссылкам в нём взяться неоткуда.
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <VCard variant="outlined" rounded="lg">
    <VCardTitle class="text-h6">{{ title }}</VCardTitle>
    <p v-if="description" class="settings-group__desc">{{ description }}</p>
    <VDivider />
    <VCardText class="d-flex flex-column ga-6">
      <slot />
    </VCardText>
  </VCard>
</template>

<style scoped>
.settings-group__desc {
  margin: 0;
  padding: 0 16px 16px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-muted);
}
</style>
