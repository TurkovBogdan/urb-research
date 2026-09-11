<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import ErrorState from '@/components/ErrorState.vue'
import { ERROR_KINDS, type ErrorKind } from '@/constants/errors'

// Единственный способ показать экран отказа: вид → иконка, код, тексты и выходы берутся из
// каталога, а не собираются на месте. Второй способ развёл бы формулировки по вьюхам.

const props = defineProps<{ kind: ErrorKind }>()

const { t } = useI18n()

const spec = computed(() => ERROR_KINDS[props.kind])
</script>

<template>
  <PageLayout>
    <ErrorState
      :icon="spec.icon"
      :code="spec.code"
      :title="t(`common.errors.${spec.key}.title`)"
      :description="t(`common.errors.${spec.key}.description`)"
      :actions="spec.actions"
    />
  </PageLayout>
</template>
