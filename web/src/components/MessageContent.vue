<script setup lang="ts">
/**
 * Renders an email body in one of two views — driven entirely by global settings, no
 * controls of its own (the view/safety switch lives once per page).
 *
 * The caller provides pre-built data: `html` is the original markup in reading order
 * with forwarded/history wrapped in <details> spoilers;
 * `text` is the same blocks as literal text (images kept as ![alt](src)). The text view is
 * rendered verbatim by MessageBody — NOT as Markdown — so e-mail punctuation (a leading `#`,
 * `1.`, `>`) is never reinterpreted as headings/lists/quotes. The view mode and the safety
 * flag are global user settings (stores/settings.ts → message.mode / message.unsafe), so every
 * message in the app follows the same preference and it persists.
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import SafeEmailBody from '@/components/SafeEmailBody.vue'
import MessageBody from '@/components/MessageBody.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import { useSettingsStore } from '@/stores/settings'

export interface MessageContentText {
  forwarded: string
  message: string
  history: string
}

defineProps<{
  html: string
  text: MessageContentText
}>()

const { t } = useI18n()
const settings = useSettingsStore()

const lightboxSrc = ref<string | null>(null)

// The backend leaves spoiler summaries empty and tags them by kind (mc-forwarded /
// mc-history); supply the localized label to the iframe via CSS ::after, so the domain
// service stays locale-free and the label follows the app language like the text view.
const spoilerFixes = computed(
  () =>
    `.mc-forwarded>summary::after{content:"${t('common.message.forwarded')}"}` +
    `.mc-history>summary::after{content:"${t('common.message.history')}"}`,
)
</script>

<template>
  <div class="message-content">
    <SafeEmailBody
      v-show="settings.message.mode === 'html'"
      :body="html"
      force-html
      hide-bar
      :show-remote="settings.message.unsafe"
      :fixes="spoilerFixes"
    />

    <div v-show="settings.message.mode !== 'html'" class="message-content__text">
      <details v-if="text.forwarded" class="message-content__spoiler">
        <summary>{{ t('common.message.forwarded') }}</summary>
        <MessageBody
          :text="text.forwarded"
          compact
          :show-remote="settings.message.unsafe"
          class="message-content__block message-content__block--quoted"
          @image-click="lightboxSrc = $event"
        />
      </details>

      <MessageBody
        :text="text.message"
        compact
        :show-remote="settings.message.unsafe"
        class="message-content__block"
        @image-click="lightboxSrc = $event"
      />

      <details v-if="text.history" class="message-content__spoiler">
        <summary>{{ t('common.message.history') }}</summary>
        <MessageBody
          :text="text.history"
          compact
          :show-remote="settings.message.unsafe"
          class="message-content__block message-content__block--quoted"
          @image-click="lightboxSrc = $event"
        />
      </details>
    </div>

    <ImageLightbox v-model="lightboxSrc" />
  </div>
</template>

<style scoped>
.message-content {
  width: 100%;
}

.message-content__text {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-content__block {
  word-break: break-word;
}

.message-content__block--quoted {
  padding-left: 24px;
}

/* Minimal spoiler — borderless chevron + uppercase faint label, matching the Spoiler
   component's `minimal` variant and the HTML view (SafeEmailBody FRAME_FIXES_CSS). */
.message-content__spoiler > summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  list-style: none;
  padding: 4px 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-faint);
  transition: color 0.15s ease;
}
.message-content__spoiler > summary::-webkit-details-marker {
  display: none;
}
.message-content__spoiler > summary::before {
  content: "";
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
  transition: transform 0.2s ease;
}
.message-content__spoiler[open] > summary::before {
  transform: rotate(90deg);
}
.message-content__spoiler > summary:hover {
  color: var(--text-muted);
}
.message-content__spoiler[open] > summary {
  margin-bottom: 6px;
}
</style>
