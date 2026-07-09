<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconArrowLeft, IconHome, type Icon } from '@tabler/icons-vue'

defineProps<{
  code?: string
  icon: Icon
  title: string
  description: string
}>()

const router = useRouter()
const { t } = useI18n()

function goBack() {
  router.back()
}
function goHome() {
  router.push('/home')
}
</script>

<template>
  <div class="error-state">
    <component :is="icon" class="error-state__icon" :size="56" stroke="1.5" />
    <span v-if="code" class="error-state__code">{{ code }}</span>
    <h1 class="error-state__title">{{ title }}</h1>
    <p class="error-state__text">{{ description }}</p>

    <div class="error-state__actions">
      <VBtn variant="outlined" size="large" @click="goBack">
        <template #prepend>
          <IconArrowLeft :size="18" />
        </template>
        {{ t('common.errors.action.back') }}
      </VBtn>
      <VBtn color="primary" size="large" flat @click="goHome">
        <template #prepend>
          <IconHome :size="18" />
        </template>
        {{ t('common.errors.action.home') }}
      </VBtn>
    </div>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 100%;
  padding: 24px;
}

.error-state__icon {
  color: var(--text-faint);
}

.error-state__code {
  margin-top: 12px;
  font-family: var(--font-mono);
  font-size: 56px;
  font-weight: 600;
  line-height: 1;
  color: var(--text);
}

.error-state__title {
  margin: 8px 0 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
}

.error-state__text {
  margin: 8px 0 0;
  max-width: 420px;
  font-size: 14px;
  color: var(--text-muted);
}

.error-state__actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}
</style>
