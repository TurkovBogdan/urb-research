<script setup lang="ts">
defineOptions({ inheritAttrs: false })

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconTrash, IconAlertTriangle, IconInfoCircle } from '@tabler/icons-vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const basicOpen      = ref(false)
const formOpen       = ref(false)
const destructiveOpen = ref(false)
const alertOpen      = ref(false)
const scrollOpen     = ref(false)

const formName  = ref('')
const formEmail = ref('')
const formSaving = ref(false)

const { t } = useI18n()

async function fakeSubmit() {
  formSaving.value = true
  await new Promise(r => setTimeout(r, 800))
  formSaving.value = false
  formOpen.value = false
}
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.dialogs.title')" :description="t('design-system.page.dialogs.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.dialogs.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">basic</span>
          <div class="ds-controls">
            <VBtn variant="outlined" @click="basicOpen = true">Open</VBtn>
          </div>
          <span class="ds-spec">title · text · buttons</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">form</span>
          <div class="ds-controls">
            <VBtn variant="outlined" @click="formOpen = true">Open</VBtn>
          </div>
          <span class="ds-spec">input fields · validation</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">destructive</span>
          <div class="ds-controls">
            <VBtn variant="outlined" color="error" @click="destructiveOpen = true">Delete…</VBtn>
          </div>
          <span class="ds-spec">confirm a dangerous action</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">alert</span>
          <div class="ds-controls">
            <VBtn variant="outlined" @click="alertOpen = true">Open</VBtn>
          </div>
          <span class="ds-spec">informational message</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">scroll</span>
          <div class="ds-controls">
            <VBtn variant="outlined" @click="scrollOpen = true">Open</VBtn>
          </div>
          <span class="ds-spec">long content · inner scroll</span>
        </div>

      </div>
    </section>

  </div>

  <!-- ── Basic ── -->
  <VDialog v-model="basicOpen" max-width="440">
    <VCard>
      <VCardTitle>Save changes?</VCardTitle>
      <VDivider />
      <VCardText>
        Unsaved changes will be lost. Do you want to save before leaving?
      </VCardText>
      <VDivider />
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" @click="basicOpen = false">Cancel</VBtn>
        <VBtn variant="text" @click="basicOpen = false">Don't save</VBtn>
        <VBtn color="primary" @click="basicOpen = false">Save</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ── Form ── -->
  <VDialog v-model="formOpen" max-width="480">
    <VCard>
      <VCardTitle>New user</VCardTitle>
      <VDivider />
      <VCardText>
        <VTextField
          v-model="formName"
          label="Name"
          density="compact"
          variant="outlined"
          class="mb-3"
          hide-details
        />
        <VTextField
          v-model="formEmail"
          label="Email"
          type="email"
          density="compact"
          variant="outlined"
          hide-details
        />
      </VCardText>
      <VDivider />
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" :disabled="formSaving" @click="formOpen = false">Cancel</VBtn>
        <VBtn color="primary" :loading="formSaving" @click="fakeSubmit">Create</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ── Destructive ── -->
  <VDialog v-model="destructiveOpen" max-width="420">
    <VCard>
      <VCardTitle class="d-flex align-center ga-2">
        <VIcon :icon="IconTrash" size="18" color="error" />
        Delete server?
      </VCardTitle>
      <VDivider />
      <VCardText>
        You are about to delete <strong>scrapper-1</strong>.
        Related data (uptime, requests) will also be gone. This action cannot be undone.
      </VCardText>
      <VDivider />
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" @click="destructiveOpen = false">Cancel</VBtn>
        <VBtn color="error" variant="flat" @click="destructiveOpen = false">Delete</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ── Alert ── -->
  <VDialog v-model="alertOpen" max-width="400">
    <VCard>
      <VCardTitle class="d-flex align-center ga-2">
        <VIcon :icon="IconInfoCircle" size="18" color="info" />
        Authorization required
      </VCardTitle>
      <VDivider />
      <VCardText>
        The browser is not signed in to hh.ru. Launch the browser, log into your account, then retry the action.
      </VCardText>
      <VDivider />
      <VCardActions>
        <VSpacer />
        <VBtn color="primary" @click="alertOpen = false">Got it</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ── Scroll ── -->
  <VDialog v-model="scrollOpen" max-width="480">
    <VCard>
      <VCardTitle>Terms of use</VCardTitle>
      <VDivider />
      <VCardText class="scroll-body">
        <p v-for="n in 12" :key="n" class="mb-3">
          Paragraph {{ n }}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
          Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim
          ad minim veniam quis nostrud exercitation.
        </p>
      </VCardText>
      <VDivider />
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" @click="scrollOpen = false">Decline</VBtn>
        <VBtn color="primary" @click="scrollOpen = false">Accept</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
  </PageLayout>

</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
}

.ds-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }

.scroll-body {
  max-height: 260px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}
</style>
