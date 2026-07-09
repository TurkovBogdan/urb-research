<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import MessageContent, { type MessageContentText } from '@/components/MessageContent.vue'
import MessageViewControls from '@/components/MessageViewControls.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'

const { t } = useI18n()

// Samples are shaped like a message-view payload: `html` is the assembled markup with
// <details> spoilers, `text` is the markup-free triple. The reply
// carries a remote banner image so the safety toggle has something to block/reveal.
interface Sample {
  html: string
  text: MessageContentText
}

const reply: Sample = {
  html:
    '<p>Hi Anna,</p>' +
    '<p>Thanks for the update — looks good to me. Let\'s ship on Friday.</p>' +
    '<p><img src="https://picsum.photos/seed/semaphore/480/120" alt="release banner"></p>' +
    '<p>Best,<br>John</p>' +
    '<details class="mc-spoiler mc-history"><summary></summary><div class="mc-quote">' +
    '<blockquote>On Mon, 15 Jun 2026, Anna &lt;anna@acme.example&gt; wrote:<br>' +
    'Here is the latest draft, let me know what you think.</blockquote></div></details>',
  text: {
    forwarded: '',
    message:
      'Hi Anna,\n\nThanks for the update — looks good to me. Let\'s ship on Friday.\n\n' +
      '![release banner](https://picsum.photos/seed/semaphore/480/120)\n\nBest,\nJohn',
    history: 'On Mon, 15 Jun 2026, Anna <anna@acme.example> wrote:\nHere is the latest draft, let me know what you think.',
  },
}

// Images-first sample: the formatting view gates the remote images behind the safety toggle,
// the text view renders them as Markdown ![alt](src) with the hover-zoom + lightbox affordance.
const withImages: Sample = {
  html:
    '<p>Here is the dashboard you asked about — the new volume chart is live:</p>' +
    '<p><img src="https://picsum.photos/seed/dashboard/520/300" alt="analytics dashboard"></p>' +
    '<p>And a close-up of the filter bar:</p>' +
    '<p><img src="https://picsum.photos/seed/filterbar/360/140" alt="filter bar"></p>',
  text: {
    forwarded: '',
    message:
      'Here is the dashboard you asked about — the new volume chart is live:\n\n' +
      '![analytics dashboard](https://picsum.photos/seed/dashboard/520/300)\n\n' +
      'And a close-up of the filter bar:\n\n' +
      '![filter bar](https://picsum.photos/seed/filterbar/360/140)',
    history: '',
  },
}

const forwarded: Sample = {
  html:
    '<details class="mc-spoiler mc-forwarded"><summary></summary><div class="mc-quote">' +
    '<p>From: billing@acme.example<br>Subject: Invoice #2026-05</p>' +
    '<p>Your invoice is attached. Total: €240.</p></div></details>' +
    '<p>FYI — forwarding the invoice for your records.</p>',
  text: {
    forwarded: 'From: billing@acme.example\nSubject: Invoice #2026-05\n\nYour invoice is attached. Total: €240.',
    message: 'FYI — forwarding the invoice for your records.',
    history: '',
  },
}

const plain: Sample = {
  html:
    '<div style="white-space:pre-wrap">Hello team,\n\nQuick reminder about tomorrow\'s standup at 10:00.</div>' +
    '<details class="mc-spoiler mc-history"><summary></summary><div class="mc-quote">' +
    '<div style="white-space:pre-wrap">On Mon, someone wrote:\n&gt; Are we still on for the standup?</div></div></details>',
  text: {
    forwarded: '',
    message: 'Hello team,\n\nQuick reminder about tomorrow\'s standup at 10:00.',
    history: 'On Mon, someone wrote:\n> Are we still on for the standup?',
  },
}

// A reaction-style image inline with text — exercises the inline alignment (the image must sit
// on the sentence line, not as a block on its own row). A data: SVG so it renders regardless of
// the safety toggle (data: is never gated as remote).
const REACTION_THUMB =
  'data:image/svg+xml,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4a90d9">' +
      '<path d="M2 21h4V9H2zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 ' +
      '7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73z"/></svg>',
  )

const reaction: Sample = {
  html: `<p><img src="${REACTION_THUMB}"> Tess Roehrig reacted to your message: looks great!</p>`,
  text: {
    forwarded: '',
    message: `![reaction](${REACTION_THUMB}) Tess Roehrig reacted to your message: looks great!`,
    history: '',
  },
}

const usageSnippet = `<script setup lang="ts">
import MessageContent from '@/components/MessageContent.vue'

// view: { html, text: { forwarded, message, history } } — built by the backend
const view = await fetchMessageView(id)
<\/script>

<template>
  <MessageContent :html="view.html" :text="view.text" />
<\/template>`

const dataSnippet = `{
  "html": "<p>Hi Anna…</p><details><summary>Quoted history</summary>…</details>",
  "text": {
    "forwarded": "",
    "message": "Hi Anna,\\n\\nThanks for the update…",
    "history": "On Mon, 15 Jun 2026, Anna wrote:\\n…"
  }
}`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.message.title')" :description="t('design-system.page.message.description')" back-to="/design-system" />

    <!-- Settings — MessageViewControls writes to the global store; every preview reacts. -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.controls') }}</h6>
      <MessageViewControls />
      <p class="ds-note">{{ t('design-system.section.message.note') }}</p>
    </VCard>

    <!-- Safe-only — hide-format drops the formatting/text switch, leaving the safety toggle alone. -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.controls_safe') }}</h6>
      <MessageViewControls hide-format />
      <p class="ds-note">{{ t('design-system.section.message.controls_safe_note') }}</p>
    </VCard>

    <!-- The component renders no card of its own; the demo wraps it in the real chat bubble
         (ChatMessage), on a gray feed-like stage, exactly as the conversation views do — so the
         preview inherits the bubble's typography and white-space, not a bare card surface. -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.reply') }}</h6>
      <div class="ds-message-stage">
        <ChatMessage side="right" tone="accent" author="john@acme.example" time="14:32">
          <MessageContent :html="reply.html" :text="reply.text" />
        </ChatMessage>
      </div>
    </VCard>

    <!-- Forwarded message -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.forward') }}</h6>
      <div class="ds-message-stage">
        <ChatMessage side="left" tone="surface" author="me@acme.example" time="09:10">
          <MessageContent :html="forwarded.html" :text="forwarded.text" />
        </ChatMessage>
      </div>
    </VCard>

    <!-- Plain text -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.plain') }}</h6>
      <div class="ds-message-stage">
        <ChatMessage side="left" tone="surface" author="team@acme.example" time="08:00">
          <MessageContent :html="plain.html" :text="plain.text" />
        </ChatMessage>
      </div>
    </VCard>

    <!-- Inline image (reaction) — sits on the text line, not on its own row -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.reaction') }}</h6>
      <div class="ds-message-stage">
        <ChatMessage side="left" tone="surface" author="tess@acme.example" time="01:46">
          <MessageContent :html="reaction.html" :text="reaction.text" />
        </ChatMessage>
      </div>
      <p class="ds-note">{{ t('design-system.section.message.reaction_note') }}</p>
    </VCard>

    <!-- Images — hover-zoom + lightbox in text view, safety gating in formatting view -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.images') }}</h6>
      <div class="ds-message-stage">
        <ChatMessage side="left" tone="surface" author="dev@acme.example" time="16:20">
          <MessageContent :html="withImages.html" :text="withImages.text" />
        </ChatMessage>
      </div>
      <p class="ds-note">{{ t('design-system.section.message.images_note') }}</p>
    </VCard>

    <!-- Usage -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.message.usage') }}</h6>
      <p class="ds-sublabel">{{ t('design-system.section.message.example') }}</p>
      <CodeBlock :code="usageSnippet" lang="vue" />
      <p class="ds-sublabel ds-sublabel--gap">{{ t('design-system.section.message.data') }}</p>
      <p class="ds-note">{{ t('design-system.section.message.data_note') }}</p>
      <CodeBlock :code="dataSnippet" lang="json" />
    </VCard>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ds-card {
  padding: 16px;
}

.ds-card__title {
  margin: 0 0 12px;
}


/* The stage where the component renders — a gray surface that sets the message apart
   from the card. */
.ds-message-stage {
  padding: 16px;
  background: var(--bg);
  border-radius: var(--radius);
}

.ds-sublabel {
  margin: 0 2px 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.ds-sublabel--gap {
  margin-top: 20px;
}

.ds-note {
  margin: 12px 2px 0;
  font-size: 12px;
  color: var(--text-faint);
}
</style>
