<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { IconError404 } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import ErrorState from '@/components/ErrorState.vue'

const { t } = useI18n()
</script>

<template>
  <PageLayout>
    <ErrorState
      :icon="IconError404"
      :title="t('common.errors.notFound.title')"
      :description="t('common.errors.notFound.description')"
    />
  </PageLayout>
</template>
