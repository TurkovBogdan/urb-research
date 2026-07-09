<script setup lang="ts">
/**
 * View controls for email-message rendering — the view-mode switch (formatting / text)
 * and the "disable safe view" switch (default off → safe view on). Bare row: no card, panel
 * or background; fills the available width. Reads and writes the global settings
 * (stores/settings.ts → message.mode / unsafe), so one instance per page steers every
 * MessageContent on it.
 *
 * `hideFormat` drops the formatting/text switch and keeps only the safe-view switch — for
 * single-message contexts where the format choice isn't offered, only the safe-view gate.
 */
import { useI18n } from 'vue-i18n'
import { IconCode, IconAlignLeft } from '@tabler/icons-vue'

import { useSettingsStore } from '@/stores/settings'

defineProps<{ hideFormat?: boolean }>()

const { t } = useI18n()
const settings = useSettingsStore()
</script>

<template>
  <div class="msg-view-controls">
    <VBtnToggle
      v-if="!hideFormat"
      :model-value="settings.message.mode"
      mandatory
      density="compact"
      variant="outlined"
      divided
      @update:model-value="settings.message.mode = $event"
    >
      <VBtn value="html" size="small" :prepend-icon="IconCode">{{ t('common.message.view_html') }}</VBtn>
      <VBtn value="text" size="small" :prepend-icon="IconAlignLeft">{{ t('common.message.view_text') }}</VBtn>
    </VBtnToggle>

    <VSwitch
      :model-value="settings.message.unsafe"
      color="warning"
      density="compact"
      hide-details
      :label="t('common.message.disable_safe')"
      class="msg-view-controls__safe"
      @update:model-value="settings.message.unsafe = !!$event"
    />
  </div>
</template>

<style scoped>
.msg-view-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 20px;
  width: 100%;
}

/* Push the safety toggle to the far end so the row spans the available width. */
.msg-view-controls__safe {
  margin-left: auto;
  flex: none;
}
</style>
