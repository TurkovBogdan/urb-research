<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import StatusBadge from '@/components/StatusBadge.vue'

import ResearchBody from '../components/ResearchBody.vue'
import TitleEditor from '../components/TitleEditor.vue'
import { useNoteDetailStore } from '../stores/note-detail.store'
import { NOTE_KIND_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const store = useNoteDetailStore()

// KeepAlive-safe reload (see ResearchView).
function reload() {
  const code = route.params.code
  if (typeof code === 'string' && code) store.load(code)
}
onActivated(reload)
watch(() => route.params.code, reload)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.note.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.note">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div class="note-head">
            <TitleEditor
              class="note-title"
              :title="store.note.title"
              :label="t('research.note.detail.title_label')"
              :saving="store.renaming"
              @save="store.rename"
            />
            <StatusBadge :color="NOTE_KIND_COLOR[store.note.kind]">
              {{ t(`research.note.kind.${store.note.kind}`) }}
            </StatusBadge>
          </div>
          <div v-if="store.note.description" class="note-desc">{{ store.note.description }}</div>
        </VCardText>
      </VCard>

      <VCard variant="outlined" rounded="lg">
        <VCardText>
          <ResearchBody v-if="store.note.body" :text="store.note.body" />
          <div v-else class="empty text-medium-emphasis">
            {{ t('research.note.detail.no_body') }}
          </div>
        </VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.note-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

/* Кегль строки редактора задаётся его же токенами: подменять `font-size` снаружи нельзя —
   на нём держится равная высота покоя и правки. Ширину строка забирает всю свободную, иначе
   бейдж типа прилипал бы к названию вместо правого края. */
.note-title {
  flex: 1 1 auto;
  min-width: 0;
  --ile-size: 16px;
}

.note-desc {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-muted);
}

.empty {
  padding: 16px 0;
  text-align: center;
}
</style>
