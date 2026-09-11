<script setup lang="ts">
// Диагноз подключения одним значком. Отсутствие подключения — тоже диагноз («не подключён»),
// поэтому status допускает null: пользователь должен видеть разницу между «сервис не
// настроен» и «сервис отвечает ошибкой».
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { AccessStatus } from '../api'

const props = defineProps<{ status: AccessStatus | null }>()

const { t } = useI18n()

const code = computed(() => props.status?.status ?? 'absent')

const TONE: Record<string, string> = {
  ok: 'is-ok',
  error: 'is-error',
  undecryptable: 'is-error',
  unconfigured: 'is-warn',
  disabled: 'is-off',
  absent: 'is-off',
}
</script>

<template>
  <span class="status" :class="TONE[code]" :title="status?.detail ?? undefined">
    {{ t(`core_connectors.status.${code}`) }}
  </span>
</template>

<style scoped>
.status {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 5px;
  white-space: nowrap;
  color: var(--text-muted);
  background: var(--border);
}

.status.is-ok { color: var(--accent); background: var(--accent-soft); }
.status.is-warn { color: var(--warn); background: var(--border); }
.status.is-error { color: var(--error); background: var(--border); }
.status.is-off { color: var(--text-muted); background: var(--border); }
</style>
