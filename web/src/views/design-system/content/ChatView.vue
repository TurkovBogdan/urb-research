<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { IconUser, IconUserCheck, IconRobot, IconNote, IconBolt, IconSparkles, IconDeviceFloppy, IconPencil } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import ChatFeed from '@/components/chat/ChatFeed.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatEvent from '@/components/chat/ChatEvent.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import MessageContent, { type MessageContentText } from '@/components/MessageContent.vue'
import MessageViewControls from '@/components/MessageViewControls.vue'
import FileCards, { type FileCardItem } from '@/components/FileCards.vue'
import { fmtDateTime, fmtRelative, fmtTime } from '@/shared/utils/date'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// The conversation feed renders each bubble through the real MessageContent component, so the
// MessageViewControls in the toolbar (global html/text + safety) drives them exactly as the
// conversation views do. prose() shapes a plain reply into both views build_message_view emits.
interface MessageBody {
  html: string
  text: MessageContentText
}

function prose(message: string): MessageBody {
  return {
    html: message.split('\n\n').map((paragraph) => `<p>${paragraph}</p>`).join(''),
    text: { forwarded: '', message, history: '' },
  }
}

// Backend-shaped UTC timestamps ("YYYY-MM-DD HH:MM:SS"); the date utils render them in
// the user's timezone + chosen format, exactly like the real conversation views.
const ts = {
  m1:  '2026-06-14 10:02:00',
  a1:  '2026-06-14 10:03:00',
  m2:  '2026-06-14 10:05:00',
  m3:  '2026-06-14 10:08:00',
  m4:  '2026-06-14 10:09:00',
  m5:  '2026-06-14 10:11:00',
  m6:  '2026-06-14 10:14:00',
  m7:  '2026-06-14 10:14:30',
  m8:  '2026-06-14 10:16:00',
  m9:  '2026-06-14 10:19:00',
  m10: '2026-06-14 10:20:00',
  n1:  '2026-06-14 10:20:40',
  n2:  '2026-06-14 10:21:10',
  m11: '2026-06-14 10:22:00',
  sample: '2026-06-14 09:30:00',
  e1: '2026-06-14 08:55:00',
  e2: '2026-06-14 08:56:00',
  e3: '2026-06-14 09:01:00',
  e4: '2026-06-14 09:04:00',
  e5: '2026-06-14 09:12:00',
}

const sampleFiles: FileCardItem[] = [
  { key: 1, filename: 'reset-steps.pdf', mime: 'application/pdf', size: 188_416, safety: 'safe', url: '#' },
  { key: 2, filename: 'logo.png', mime: 'image/png', size: 42_000, safety: 'safe', url: '#' },
  { key: 3, filename: 'account-export.csv', mime: 'text/csv', size: 12_800, safety: 'safe', url: '#' },
  { key: 4, filename: 'screenshot-error.png', mime: 'image/png', size: 318_000, safety: 'safe', url: '#' },
]

const clientFiles: FileCardItem[] = [
  { key: 5, filename: 'login-loop.gif', mime: 'image/gif', size: 1_204_000, safety: 'safe', url: '#' },
  { key: 6, filename: 'console-log.txt', mime: 'text/plain', size: 7_400, safety: 'warning', url: '#' },
]

const invoiceFiles: FileCardItem[] = [
  { key: 7, filename: 'invoice-2026-05.pdf', mime: 'application/pdf', size: 96_200, safety: 'safe', url: '#' },
  { key: 8, filename: 'invoice-2026-04.pdf', mime: 'application/pdf', size: 94_800, safety: 'safe', url: '#' },
]

const bodies: Record<string, MessageBody> = {
  m1: prose("Hi there! Since this morning I can't log into my account at all. I type my email and password, the page reloads for a second, and then it just throws me back to the login screen without any error message. I've tried Chrome, Safari and even a private window — same thing everywhere. This is pretty urgent because I have a client demo scheduled for this afternoon and all my saved templates live inside the account. Could you take a look as soon as possible?"),
  m2: {
    html:
      "<p>Hello Jane, thanks for the detailed description — that really helps narrow it down. I can see your account on our side and you're right: a password-reset job got stuck in a half-finished state last night, which is why the session never sticks after login.</p>" +
      "<p>Nothing is lost, your templates and history are all intact. I'm clearing the stuck job now and sending you a fresh reset link. I've also attached a short PDF with the exact steps and our logo so you know the email is genuinely from us.</p>" +
      '<p><img src="https://picsum.photos/seed/semaphore-logo/420/120" alt="brand logo"></p>',
    text: {
      forwarded: '',
      message:
        "Hello Jane, thanks for the detailed description — that really helps narrow it down. I can see your account on our side and you're right: a password-reset job got stuck in a half-finished state last night, which is why the session never sticks after login.\n\n" +
        "Nothing is lost, your templates and history are all intact. I'm clearing the stuck job now and sending you a fresh reset link. I've also attached a short PDF with the exact steps and our logo so you know the email is genuinely from us.\n\n" +
        "![brand logo](https://picsum.photos/seed/semaphore-logo/420/120)",
      history: '',
    },
  },
  agent: prose("Hi Jane — I'm the support assistant. While an agent picks up your case, a quick thing to try: open a fresh private window and clear cookies for our domain, since a stale session cookie causes most login loops. I've also queued a health check on your account and flagged this thread for a human agent."),
  m3: prose("Thanks, I got the email! The reset page asks for an 'existing security code' before it lets me set a new password, and I don't think I ever set one up. Is that field expected, or can I skip it?"),
  noteM4: prose("Internal note: this is the third stuck-reset report this week — all trace back to the same worker lock not being released on shutdown. The auto-clear guard is a band-aid; we should open a proper ticket to fix the lock lifecycle in the reset worker before it bites a bigger customer. Watching for a recurring auth bug."),
  m5: prose("Good catch — that security-code field is optional and only applies to accounts with 2FA, which yours doesn't have. Just leave it blank and set your new password directly. Let me know once you're through and whether the login loop is finally gone."),
  m6: prose("That did it — I left the field blank, set a new password, and I'm finally back in. All my templates are exactly where they should be, what a relief. Thank you for the quick turnaround! I'm attaching a short screen recording of the old login loop and the browser console log in case it helps you track down the root cause."),
  m7: prose("Password reset completed for jane@example.com. The previous stuck reset token was invalidated, and the account was flagged for a follow-up health check in 24 hours to make sure the login loop does not return."),
  m8: prose("Perfect, glad you're sorted. I'll keep this conversation open until tomorrow's automated health check passes, then close it out. Good luck with the demo this afternoon!"),
  m9: prose("Sounds good, thank you. One more thing while I have you — is there anything I can do on my end to avoid this happening again?"),
  m10: prose("…or was it purely on the server side? Just want to be sure nothing bites me right before the demo."),
  noteN1: prose("Internal note: looping in support — the root cause is confirmed server-side, so there is nothing for the client to do. Closing the loop once the health check passes tomorrow."),
  noteN2: prose("Internal note: filed ticket OPS-482 to fix the worker lock lifecycle properly so the auto-clear guard can eventually be removed. Linking this conversation as the third repro this week."),
  m11: prose("Entirely on our side — nothing you did and nothing for you to change. We've already shipped a guard that auto-recovers from these stuck jobs within a minute, so even in the unlikely case it recurs it won't lock you out again. Enjoy the demo!"),
}

// The composer demo is a live thread: a seeded log of prior messages with the composer pinned
// below. Sending appends an outgoing bubble stamped at the current time and re-pins to the bottom.
interface ChatLogEntry {
  id: number
  side: 'left' | 'right'
  tone: 'surface' | 'accent'
  author: string
  body: string
  time: string
}

const composerLog = ref<ChatLogEntry[]>([
  { id: 1, side: 'left', tone: 'surface', author: 'Jane Client', time: fmtDateTime(ts.m9), body: "Sounds good, thank you. One more thing while I have you — is there anything I can do on my end to avoid this happening again?" },
  { id: 2, side: 'right', tone: 'accent', author: 'Bogdan (admin)', time: fmtDateTime(ts.m11), body: "Entirely on our side — nothing you did and nothing for you to change. We've already shipped a guard that auto-recovers from these stuck jobs within a minute." },
  { id: 3, side: 'left', tone: 'surface', author: 'Jane Client', time: fmtDateTime(ts.m11), body: "Perfect, that's reassuring. I'll go run the demo now — thanks again for the fast turnaround!" },
])
let nextLogId = composerLog.value.length + 1

const composerQuickReplies = [
  { label: 'Greeting', text: "Hi! Thanks for reaching out — I'm happy to help. Could you share a few more details so I can dig into this for you?" },
  { label: 'Investigating', text: "Thanks for your patience — I'm looking into this on our side right now and will follow up as soon as I have something concrete." },
  { label: 'Resolved', text: "This should be sorted now. Could you confirm everything works on your end? If anything still looks off, just let me know and I'll jump back in." },
  { label: 'Closing', text: "Glad we got this resolved! I'll close the conversation for now — feel free to reopen it any time if you need anything else." },
]

const composerFeed = ref<InstanceType<typeof ChatFeed>>()

function nowTimestamp(): string {
  return new Date().toISOString().slice(0, 19).replace('T', ' ')
}

async function onComposerSend(text: string) {
  composerLog.value.push({
    id: nextLogId++,
    side: 'right',
    tone: 'accent',
    author: 'Bogdan (admin)',
    body: text,
    time: fmtDateTime(nowTimestamp()),
  })
  await nextTick()
  composerFeed.value?.scrollToBottom()
}

// The first showcase feed is a full chat window: the static thread above plus a live composer.
// Replies typed there append below the seeded messages.
interface SentReply {
  id: number
  body: string
  time: string
}

const feedReplies = ref<SentReply[]>([])
let nextReplyId = 1
const mainFeed = ref<InstanceType<typeof ChatFeed>>()

async function onFeedSend(text: string) {
  feedReplies.value.push({ id: nextReplyId++, body: text, time: fmtDateTime(nowTimestamp()) })
  await nextTick()
  mainFeed.value?.scrollToBottom()
}

// Agent-instruction block: a standing comment for the AI model, bound to a specific contact.
// Switching the contact loads that contact's instruction into the bubble and the editor below;
// the bubble shows the saved text, the composer edits it, and Save commits the draft back.
interface InstructionContact {
  id: number
  name: string
  instruction: string
  author: string
  updatedAt: string
}

const instructionContacts = ref<InstructionContact[]>([
  { id: 1, name: 'Jane Client', author: 'Bogdan (admin)', updatedAt: '2026-06-16 14:30:00', instruction: "Long-time customer on the Business plan — keep replies warm and concise. She runs live demos in the afternoons, so flag anything urgent and avoid scheduling downtime before 18:00." },
  { id: 2, name: 'Acme Co. · billing', author: 'Anna (support lead)', updatedAt: '2026-06-17 09:15:00', instruction: "Route every billing question to a human before promising refunds. The account has an open invoice dispute (OPS-482) — never quote amounts; defer to the finance team." },
  { id: 3, name: 'New lead (no history)', author: '', updatedAt: '', instruction: '' },
])
const selectedContactId = ref(1)
const selectedContact = computed(
  () => instructionContacts.value.find((c) => c.id === selectedContactId.value) ?? instructionContacts.value[0],
)

// The composer starts empty; Edit loads the contact's current instruction into it for editing.
// Switching the contact clears the editor again (its block above already shows the saved text).
const instructionDraft = ref('')
watch(selectedContactId, () => { instructionDraft.value = '' })

const instructionComposer = ref<InstanceType<typeof ChatComposer>>()

function editInstruction() {
  instructionDraft.value = selectedContact.value.instruction
  nextTick(() => instructionComposer.value?.focus())
}

function saveInstruction(text: string) {
  selectedContact.value.instruction = text
  selectedContact.value.author = 'Bogdan (admin)'
  selectedContact.value.updatedAt = nowTimestamp()
}

const slotsSchema = `ChatFeed
├─ #toolbar       non-scrolling header bar (blocked-images notice, actions)
├─ #empty         placeholder shown when :empty
├─ default        the message stream ↓
│  ├─ ChatMessage
│  │  ├─ #meta          chips after the author (AI / note / source …)
│  │  ├─ default        bubble body — rendered via <MessageContent>
│  │  └─ #attachments   files rendered under the bubble
│  └─ ChatEvent
│     └─ default        inline system-event text
└─ #composer      optional non-scrolling input bar pinned to the bottom (ChatComposer)`

const usageSnippet = `<script setup lang="ts">
import { ref, nextTick } from 'vue'
import ChatFeed from '@/components/chat/ChatFeed.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatEvent from '@/components/chat/ChatEvent.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import MessageContent from '@/components/MessageContent.vue'
import MessageViewControls from '@/components/MessageViewControls.vue'
import { IconUser, IconUserCheck } from '@tabler/icons-vue'

const feed = ref<InstanceType<typeof ChatFeed>>()

async function load() {
  // ...fetch messages...
  await nextTick()
  feed.value?.scrollToBottom()
}

async function send(text: string) {
  // ...post the reply...
  await nextTick()
  feed.value?.scrollToBottom()
}
<\/script>

<template>
  <ChatFeed ref="feed" :empty="messages.length === 0" empty-text="No messages">
    <template #toolbar>
      <MessageViewControls />
    </template>

    <template v-for="m in messages" :key="m.id">
      <ChatEvent v-if="m.kind === 'event'" :time="fmtTime(m.ts)">
        {{ m.label }}
      </ChatEvent>
      <ChatMessage
        v-else
        :side="m.fromTeam ? 'right' : 'left'"
        :tone="m.fromTeam ? 'accent' : 'surface'"
        :author="m.author"
        :author-icon="m.fromTeam ? IconUserCheck : IconUser"
        :time="fmtDateTime(m.ts)"
      >
        <MessageContent :html="m.content.html" :text="m.content.text" />
      </ChatMessage>
    </template>

    <!-- optional: pin a composer to the bottom -->
    <template #composer>
      <ChatComposer :quick-replies="quickReplies" @send="send" />
    </template>
  </ChatFeed>
<\/template>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.chat.title')" :description="t('design-system.page.chat.description')" back-to="/design-system" />

    <!-- Conversation feed -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.feed') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed ref="mainFeed">
          <template #toolbar>
            <MessageViewControls />
          </template>

          <!-- client -->
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            author="Jane Client"
            :time="fmtDateTime(ts.m1)"
            :time-relative="fmtRelative(ts.m1)"
          >
            <MessageContent :html="bodies.m1.html" :text="bodies.m1.text" />
          </ChatMessage>
          <!-- AI agent -->
          <ChatMessage
            side="right"
            tone="muted"
            :author-icon="IconRobot"
            author="AI Agent"
            :time="fmtDateTime(ts.a1)"
            :time-relative="fmtRelative(ts.a1)"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="primary" class="ml-1">
                <template #prepend><VIcon :icon="IconRobot" size="10" /></template>
                AI
              </VChip>
            </template>
            <MessageContent :html="bodies.agent.html" :text="bodies.agent.text" />
          </ChatMessage>
          <!-- admin -->
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.m2)"
            :time-relative="fmtRelative(ts.m2)"
          >
            <MessageContent :html="bodies.m2.html" :text="bodies.m2.text" />
            <template #attachments>
              <FileCards :files="sampleFiles" />
            </template>
          </ChatMessage>
          <!-- client -->
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            author="Jane Client"
            :time="fmtDateTime(ts.m3)"
            :time-relative="fmtRelative(ts.m3)"
          >
            <MessageContent :html="bodies.m3.html" :text="bodies.m3.text" />
          </ChatMessage>
          <!-- заметка -->
          <ChatMessage
            side="right"
            tone="warning"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.m4)"
            width="86%"
            center
            divided
            :divider-label="t('design-system.section.chat.note_divider')"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="warning">
                <template #prepend><VIcon :icon="IconNote" size="10" class="me-1" /></template>
                note
              </VChip>
            </template>
            <MessageContent :html="bodies.noteM4.html" :text="bodies.noteM4.text" />
          </ChatMessage>
          <!-- admin -->
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.m5)"
            :time-relative="fmtRelative(ts.m5)"
          >
            <MessageContent :html="bodies.m5.html" :text="bodies.m5.text" />
          </ChatMessage>
          <!-- client -->
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            author="Jane Client"
            :time="fmtDateTime(ts.m6)"
            :time-relative="fmtRelative(ts.m6)"
          >
            <MessageContent :html="bodies.m6.html" :text="bodies.m6.text" />
            <template #attachments>
              <FileCards :files="clientFiles" />
            </template>
          </ChatMessage>
          <!-- автоматизация -->
          <ChatMessage
            side="left"
            tone="muted"
            :author-icon="IconRobot"
            author="Automation"
            :time="fmtDateTime(ts.m7)"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="primary" class="ml-1">
                <template #prepend><VIcon :icon="IconRobot" size="10" /></template>
                AI
              </VChip>
            </template>
            <MessageContent :html="bodies.m7.html" :text="bodies.m7.text" />
          </ChatMessage>
          <!-- admin -->
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.m8)"
            :time-relative="fmtRelative(ts.m8)"
          >
            <MessageContent :html="bodies.m8.html" :text="bodies.m8.text" />
          </ChatMessage>
          <!-- client -->
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            author="Jane Client"
            :time="fmtDateTime(ts.m9)"
            :time-relative="fmtRelative(ts.m9)"
          >
            <MessageContent :html="bodies.m9.html" :text="bodies.m9.text" />
          </ChatMessage>
          <!-- client -->
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            author="Jane Client"
            :time="fmtDateTime(ts.m10)"
            :time-relative="fmtRelative(ts.m10)"
          >
            <MessageContent :html="bodies.m10.html" :text="bodies.m10.text" />
          </ChatMessage>
          <!-- заметка -->
          <ChatMessage
            side="right"
            tone="warning"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.n1)"
            width="86%"
            center
            divided
            :divider-label="t('design-system.section.chat.note_divider')"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="warning">
                <template #prepend><VIcon :icon="IconNote" size="10" class="me-1" /></template>
                note
              </VChip>
            </template>
            <MessageContent :html="bodies.noteN1.html" :text="bodies.noteN1.text" />
          </ChatMessage>
          <!-- заметка -->
          <ChatMessage
            side="right"
            tone="warning"
            author="Anna (support lead)"
            :time="fmtDateTime(ts.n2)"
            width="86%"
            center
            divided
            :divider-label="t('design-system.section.chat.note_divider')"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="warning">
                <template #prepend><VIcon :icon="IconNote" size="10" class="me-1" /></template>
                note
              </VChip>
            </template>
            <MessageContent :html="bodies.noteN2.html" :text="bodies.noteN2.text" />
          </ChatMessage>
          <!-- admin -->
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.m11)"
            :time-relative="fmtRelative(ts.m11)"
          >
            <MessageContent :html="bodies.m11.html" :text="bodies.m11.text" />
          </ChatMessage>
          <!-- live replies typed into the composer below -->
          <ChatMessage
            v-for="m in feedReplies"
            :key="m.id"
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="m.time"
            :body="m.body"
          />

          <template #composer>
            <ChatComposer :quick-replies="composerQuickReplies" @send="onFeedSend" />
          </template>
        </ChatFeed>
      </div>
      <p class="ds-note">
        <code>ChatFeed</code> is the scrollable column (centered, max <code>width</code> 840px);
        <code>ChatMessage</code> is a bubble; <code>ChatEvent</code> is an inline system line.
        Each bubble renders its body through <code>MessageContent</code>, and the
        <code>#toolbar</code> hosts <code>MessageViewControls</code> — switching formatting/text or
        safe mode there re-renders every message. Call <code>feed.scrollToBottom()</code> after loading.
      </p>
    </VCard>

    <!-- Events & structure -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.events') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed>
          <ChatEvent :time="fmtTime(ts.e1)">Conversation opened from the contact form</ChatEvent>
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconBolt"
            author="Source · web form"
            :time="fmtDateTime(ts.e1)"
            body="Subject: Cannot download my invoices — the billing page shows a spinner forever and never lists anything. Account: acme-co. Plan: Business."
          />
          <ChatEvent :time="fmtTime(ts.e2)">Assigned to Bogdan · routed by the billing rule</ChatEvent>
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            author="Bogdan (admin)"
            :time="fmtDateTime(ts.e3)"
            :time-relative="fmtRelative(ts.e3)"
            body="Hi! Thanks for flagging this. I can reproduce the stuck spinner on the billing page for Business accounts — it's a known issue with the invoice export service timing out. I'm pulling your invoices manually and attaching them here while we ship the fix."
          >
            <template #attachments>
              <FileCards :files="invoiceFiles" />
            </template>
          </ChatMessage>
          <ChatEvent :time="fmtTime(ts.e4)">Tag added: billing · priority raised to high</ChatEvent>
          <ChatMessage
            side="left"
            tone="error"
            author="Rejected · safety filter"
            :time="fmtDateTime(ts.e4)"
            body="(message withheld) An inbound reply was quarantined because it carried an executable attachment. The text is shown here for audit only and was never delivered to the agent."
          />
          <ChatEvent :time="fmtTime(ts.e5)">Conversation snoozed until tomorrow</ChatEvent>
        </ChatFeed>
      </div>
      <p class="ds-note">
        <code>ChatEvent</code> renders inline lifecycle events (opened, assigned, tagged, snoozed)
        between bubbles. A <code>rejected</code> message kept for audit is flagged with
        <code>tone="error"</code>.
      </p>
    </VCard>

    <!-- Message kinds -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.kinds') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed>
          <ChatMessage
            side="left"
            tone="surface"
            :author-icon="IconUser"
            :author="t('design-system.section.chat.incoming')"
            :time="fmtTime(ts.sample)"
            body="Incoming — a message from the client or an external contact. Always on the left, neutral surface tone."
          />
          <ChatMessage
            side="right"
            tone="accent"
            :author-icon="IconUserCheck"
            :author="t('design-system.section.chat.outgoing')"
            :time="fmtTime(ts.sample)"
            body="Outgoing — a reply sent from our team or an admin. Always on the right, accent tone."
          />
          <ChatMessage
            side="left"
            tone="muted"
            :author-icon="IconRobot"
            :author="t('design-system.section.chat.agent')"
            :time="fmtTime(ts.sample)"
            body="Agent — a message generated by an AI agent or automation. De-emphasised muted tone with a robot icon and an AI chip, so machine output is clearly set apart from a human reply."
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="primary" class="ml-1">
                <template #prepend><VIcon :icon="IconRobot" size="10" /></template>
                AI
              </VChip>
            </template>
          </ChatMessage>
          <ChatMessage
            side="right"
            tone="warning"
            :author="t('design-system.section.chat.note')"
            :time="fmtTime(ts.sample)"
            width="86%"
            center
            divided
            :divider-label="t('design-system.section.chat.note_divider')"
          >
            <template #meta>
              <VChip size="x-small" variant="tonal" color="warning">
                <template #prepend><VIcon :icon="IconNote" size="10" class="me-1" /></template>
                note
              </VChip>
            </template>
            Note — an internal remark visible to the team only, never delivered to the client. Centered, warning tone and set off by full-width dashed rules so it can never be mistaken for a sent message.
          </ChatMessage>
        </ChatFeed>
      </div>
      <p class="ds-note">
        Four distinct entities: <code>incoming</code> (left / surface), <code>outgoing</code>
        (right / accent), <code>agent</code> (left / muted + AI chip), and <code>note</code>
        (centered / warning, set off by full-width dashed rules via <code>divided</code>), each with its own styling so a
        human reply, machine output and an internal note are never confused.
      </p>
    </VCard>

    <!-- Tones -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.tones') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed>
          <ChatMessage side="left" tone="surface" author="surface" :time="fmtTime(ts.sample)" body="Neutral incoming message — the default for anything coming from the client or an external contact. Sits on the left with a plain surface background and a soft shadow, no border." />
          <ChatMessage side="right" tone="accent" author="accent" :time="fmtTime(ts.sample)" body="Our side — a reply from the team or an admin. Aligned to the right and tinted with the accent colour so the operator's voice reads clearly against the client's neutral bubbles." />
          <ChatMessage side="left" tone="muted" author="muted" :time="fmtTime(ts.sample)" body="Automated or bot-generated message, intentionally de-emphasised with a muted grey background so system chatter never competes with the real human conversation around it." />
          <ChatMessage side="left" tone="warning" author="warning" :time="fmtTime(ts.sample)" body="Highlighted message — for example an in-thread teammate or a message that needs the reader's attention. The warm warning tint makes it stand out without an explicit border." />
          <ChatMessage side="left" tone="error" author="error" :time="fmtTime(ts.sample)" body="Faulted message — for instance one that failed to send or could not be processed. The red tint flags the problem so a failed message is never mistaken for a normal one." />
        </ChatFeed>
      </div>
      <p class="ds-note">
        <code>tone</code>: <code>surface</code> · <code>accent</code> · <code>muted</code> · <code>warning</code> · <code>error</code>.
        <code>side</code> aligns the row and squares the bottom tail corner.
      </p>
    </VCard>

    <!-- Empty state -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.empty') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed :empty="true" :empty-text="t('design-system.section.chat.no_messages')" />
      </div>
      <p class="ds-note">
        <code>empty</code> + <code>empty-text</code> render a centered placeholder; or use the <code>#empty</code> slot.
      </p>
    </VCard>

    <!-- Composer -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.composer') }}</h6>
      <div class="ds-chat-host">
        <ChatFeed ref="composerFeed">
          <ChatMessage
            v-for="m in composerLog"
            :key="m.id"
            :side="m.side"
            :tone="m.tone"
            :author-icon="m.side === 'right' ? IconUserCheck : IconUser"
            :author="m.author"
            :time="m.time"
            :body="m.body"
          />

          <template #composer>
            <ChatComposer
              :placeholder="t('design-system.section.chat.composer_placeholder')"
              :quick-replies="composerQuickReplies"
              @send="onComposerSend"
            />
          </template>
        </ChatFeed>
      </div>
      <p class="ds-note">
        The optional <code>#composer</code> slot pins a non-scrolling bar to the bottom of the feed,
        the counterpart of the top <code>#toolbar</code>. <code>ChatComposer</code> emits
        <code>send</code> with the trimmed text — Enter sends, Shift+Enter inserts a newline.
        <code>quick-replies</code> renders canned-answer chips under the field (short
        <code>label</code>, full <code>text</code> inserted at the caret on click). Omit the slot
        and the feed has no input.
      </p>
    </VCard>

    <!-- Agent instruction -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.instruction') }}</h6>
      <div class="ds-chat-host ds-chat-host--short">
        <ChatFeed>
          <template #toolbar>
            <span class="ds-chat-bar-text">{{ t('design-system.section.chat.instruction_for') }}</span>
            <VSelect
              v-model="selectedContactId"
              :items="instructionContacts"
              item-title="name"
              item-value="id"
              density="compact"
              variant="plain"
              hide-details
              :chips="false"
              class="ds-instruction-contact"
            />
          </template>

          <ChatMessage divided center width="86%">
            <template #divider>
              <span class="ds-instruction-label">
                <VIcon :icon="IconSparkles" size="13" />
                {{ t('design-system.section.chat.instruction_label') }}
              </span>
            </template>

            <div class="ds-instruction">
              <template v-if="selectedContact.instruction">
                <div class="ds-instruction__author">
                  <VIcon :icon="IconUserCheck" size="12" />
                  {{ selectedContact.author }}
                </div>
                <p class="ds-instruction__text">{{ selectedContact.instruction }}</p>
                <div class="ds-instruction__date">
                  {{ t('design-system.section.chat.instruction_updated') }} {{ fmtDateTime(selectedContact.updatedAt) }}
                </div>
              </template>
              <p v-else class="ds-instruction__empty">{{ t('design-system.section.chat.instruction_empty') }}</p>

              <div class="ds-instruction__actions">
                <VBtn
                  :prepend-icon="IconPencil"
                  size="small"
                  variant="tonal"
                  color="primary"
                  @click="editInstruction"
                >
                  {{ t('design-system.section.chat.instruction_edit') }}
                </VBtn>
              </div>
            </div>
          </ChatMessage>

          <template #composer>
            <ChatComposer
              ref="instructionComposer"
              v-model="instructionDraft"
              :placeholder="t('design-system.section.chat.instruction_placeholder')"
              :submit-icon="IconDeviceFloppy"
              cancelable
              @send="saveInstruction"
            />
          </template>
        </ChatFeed>
      </div>
      <p class="ds-note">
        A standing comment to the AI model, bound to a specific contact — rendered as a
        <code>divided</code> note block (full-bleed rules + author, text, updated date and a centered
        Edit button), not a bubble. Switch the contact in the toolbar to view its instruction. The
        composer below starts empty; <strong>Edit loads the current text into it</strong> for
        editing, then a save <code>submit-icon</code> commits it back into the block. Prototype only
        — no persistence yet.
      </p>
    </VCard>

    <!-- Usage -->
    <VCard class="ds-card">
      <h6 class="ds-card__title">{{ t('design-system.section.chat.usage') }}</h6>
      <p class="ds-sublabel">{{ t('design-system.section.chat.slots') }}</p>
      <CodeBlock :code="slotsSchema" lang="text" />
      <p class="ds-sublabel ds-sublabel--gap">{{ t('design-system.section.chat.example') }}</p>
      <CodeBlock :code="usageSnippet" lang="vue" />
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

.ds-chat-bar-text {
  font-size: 12px;
  color: var(--text-muted);
}

.ds-chat-host {
  height: 80vh;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

/* A single standing instruction needs no full-height thread. */
.ds-chat-host--short {
  height: 360px;
}

.ds-instruction-contact {
  flex: 0 0 auto;
  min-width: 0;
  max-width: 260px;
  font-weight: 600;
}

.ds-instruction {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

/* Divider label + sparkles icon in the brand colour. */
.ds-instruction-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent);
}

.ds-instruction__author {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.ds-instruction__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text);
  white-space: pre-wrap;
}

.ds-instruction__date {
  font-size: 10px;
  color: var(--text-faint);
}

.ds-instruction__empty {
  margin: 0;
  font-size: 12px;
  font-style: italic;
  color: var(--text-faint);
}

.ds-instruction__actions {
  display: flex;
  justify-content: center;
  margin-top: 4px;
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

.ds-note code {
  font-family: var(--font-mono);
  font-size: 11px;
}
</style>
