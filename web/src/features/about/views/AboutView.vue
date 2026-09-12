<script setup lang="ts">
import { computed, onActivated, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconDownload, IconGitBranch, IconInfoCircle } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { updateApi, type Installation, type UpstreamHead } from '../api'
import { waitForRestart } from '../waitForRestart'

const { t } = useI18n()

const installation = ref<Installation | null>(null)
const upstream = ref<UpstreamHead | null>(null)
const loading = ref(true)
const checking = ref(false)
const upstreamError = ref('')

const confirmOpen = ref(false)
const updating = ref(false)
const updateNote = ref('')

async function loadInstallation() {
  try {
    installation.value = await updateApi.installation()
  } finally {
    loading.value = false
  }
}

async function checkUpstream() {
  checking.value = true
  upstreamError.value = ''
  try {
    upstream.value = await updateApi.check()
  } catch {
    // Текст отказа уже показан всплывающим сообщением клиента API; здесь — состояние карточки.
    upstreamError.value = t('about.upstream.unavailable')
  } finally {
    checking.value = false
  }
}

onMounted(async () => {
  await loadInstallation()
  await checkUpstream()
})
// Возврат на страницу перечитывает только локальное: обращение к remote стоит секунд.
onActivated(() => { if (!loading.value) loadInstallation() })

const unknown = computed(() => t('about.installed.unknown'))

const buildLabel = computed(() => {
  const here = installation.value
  if (!here) return ''
  const build = here.describes_as ?? here.commit
  if (!build) return unknown.value
  return here.dirty ? `${build} · ${t('about.installed.dirty')}` : build
})

const distanceLabel = computed(() => {
  const head = upstream.value
  if (!head) return ''
  if (head.behind === null) return t('about.upstream.unknown')
  if (head.ahead) return t('about.upstream.ahead', { n: head.ahead })
  return head.behind === 0
    ? t('about.upstream.up_to_date')
    : t('about.upstream.behind', head.behind)
})

const behind = computed(() => (upstream.value?.behind ?? 0) > 0)

// Бэкенд называет причину кодом (локали у него нет) — говорит её страница.
const refusalText = computed(() => {
  const refusal = installation.value?.refusal
  return refusal ? t(`about.refusal.${refusal}`) : ''
})

async function startUpdate() {
  updating.value = true
  confirmOpen.value = false
  const versionBefore = installation.value?.commit

  let started
  try {
    started = await updateApi.start()
  } catch {
    updating.value = false
    return
  }
  updateNote.value = t('about.update.started', { pid: started.pid })

  const cameBack = await waitForRestart()
  if (!cameBack) {
    updating.value = false
    updateNote.value = t('about.update.timeout', { log: started.log })
    return
  }

  // Отказ команды (грязное дерево, недостижимый remote) оставляет бэкенд живым и версию прежней:
  // молча перезагружать страницу в этом случае — значит не сказать ничего.
  await loadInstallation()
  if (installation.value?.commit === versionBefore) {
    updating.value = false
    updateNote.value = t('about.update.unchanged', { log: started.log })
    return
  }
  window.location.reload()
}
</script>

<template>
  <PageLayout>
    <PageHeader :title="t('about.page.title')" :description="t('about.page.description')">
      <template #actions>
        <VBtn
          :color="behind ? 'primary' : undefined"
          :variant="behind ? 'flat' : 'outlined'"
          :prepend-icon="IconDownload"
          :loading="updating"
          :disabled="loading || !!refusalText"
          @click="confirmOpen = true"
        >
          {{ t('about.update.run') }}
        </VBtn>
      </template>
    </PageHeader>

    <VRow>
      <VCol cols="12" md="6">
        <VCard variant="outlined" rounded="lg" class="fact-card">
          <VCardTitle class="section-title">
            <IconInfoCircle :size="18" />
            {{ t('about.installed.title') }}
          </VCardTitle>
          <VCardText>
            <VSkeletonLoader v-if="loading" type="list-item-two-line@2" />
            <dl v-else-if="installation" class="facts">
              <dt>{{ t('about.installed.version') }}</dt>
              <dd class="facts__version">{{ installation.version ?? unknown }}</dd>

              <dt>{{ t('about.installed.release_date') }}</dt>
              <dd>{{ installation.release_date ?? '—' }}</dd>

              <dt>{{ t('about.installed.build') }}</dt>
              <dd :class="{ 'facts__warn': installation.dirty }">{{ buildLabel }}</dd>

              <dt>{{ t('about.installed.branch') }}</dt>
              <dd>
                {{ installation.followed_branch }}
                <div
                  v-if="!installation.branch_matches && installation.checked_out_branch"
                  class="facts__warn"
                >
                  {{ t('about.installed.branch_mismatch', { branch: installation.checked_out_branch }) }}
                </div>
              </dd>
            </dl>
          </VCardText>
        </VCard>
      </VCol>

      <VCol cols="12" md="6">
        <VCard variant="outlined" rounded="lg" class="fact-card">
          <VCardTitle class="section-title">
            <IconGitBranch :size="18" />
            {{ t('about.upstream.title', { branch: installation?.followed_branch ?? '—' }) }}
          </VCardTitle>
          <VCardText>
            <VSkeletonLoader v-if="checking && !upstream" type="list-item-two-line@2" />
            <div v-else-if="upstreamError" class="facts__warn">{{ upstreamError }}</div>
            <dl v-else-if="upstream" class="facts">
              <dt>{{ t('about.upstream.version') }}</dt>
              <dd class="facts__version">{{ upstream.version ?? unknown }}</dd>

              <dt>{{ t('about.upstream.commit') }}</dt>
              <dd>{{ upstream.commit }}</dd>

              <dt>{{ t('about.upstream.distance') }}</dt>
              <dd :class="{ 'facts__accent': behind, 'facts__warn': upstream.ahead }">
                {{ distanceLabel }}
              </dd>
            </dl>
          </VCardText>
          <VCardActions>
            <VBtn
              variant="text"
              :prepend-icon="IconRefresh"
              :loading="checking"
              :disabled="updating"
              @click="checkUpstream"
            >
              {{ t('about.upstream.check') }}
            </VBtn>
          </VCardActions>
        </VCard>
      </VCol>

      <VCol cols="12">
        <VCard variant="outlined" rounded="lg">
          <VCardTitle class="section-title">
            <IconDownload :size="18" />
            {{ t('about.update.title') }}
          </VCardTitle>
          <VCardText>
            <p class="update__text">{{ t('about.update.description') }}</p>
            <p v-if="refusalText" class="facts__warn">{{ refusalText }}</p>
            <p v-if="updateNote" class="update__note">{{ updateNote }}</p>
            <p v-if="updating" class="update__note">{{ t('about.update.waiting') }}</p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <ConfirmDialog
      v-model="confirmOpen"
      :title="t('about.update.confirm_title')"
      :text="t('about.update.confirm_text')"
      :confirm-label="t('about.update.confirm_ok')"
      tone="primary"
      :loading="updating"
      @confirm="startUpdate"
    />
  </PageLayout>
</template>

<style scoped>
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}

/* Две карточки-факта стоят рядом и читаются как пара, поэтому их высоту задаёт ряд, а не
   содержимое: у правой есть кнопка проверки, у левой нет, и без этого правая была бы выше. */
.fact-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.fact-card :deep(.v-card-text) {
  flex: 1;
}

.facts {
  display: grid;
  grid-template-columns: minmax(140px, auto) 1fr;
  gap: 8px 16px;
  align-items: baseline;
  margin: 0;
}

.facts dt {
  color: var(--text-muted);
}

.facts dd {
  margin: 0;
}

.facts__version {
  font-size: 20px;
  font-weight: 600;
}

.facts__warn {
  color: var(--warn);
}

.facts__accent {
  color: var(--accent);
}

.update__text {
  color: var(--text-muted);
  margin: 0;
}

.update__note {
  margin: 8px 0 0;
}
</style>
