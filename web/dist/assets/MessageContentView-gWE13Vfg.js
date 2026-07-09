import{ak as f,aN as y,ad as w,aX as n,ac as s,ai as e,aL as a,aK as o,w as i,aB as x,aa as v}from"./index-DucitkGq.js";import{_ as b}from"./PageLayout.vue_vue_type_script_setup_true_lang-BWR86Zx6.js";import{P as k}from"./PageHeader-BYf4O_Bt.js";import{C as u}from"./CodeBlock-DCPeG-aC.js";import{a as _,C as d,M as r}from"./MessageViewControls-CVtsCB3j.js";import"./IconArrowLeft-D6XlGFor.js";import"./IconCode-kIIWdYAh.js";import"./purify.es-DxCUJf2h.js";import"./IconAlertTriangle-BO_g6oAa.js";import"./IconEye-CxZ_gzqI.js";import"./IconAlignLeft-DlTj2rlZ.js";const M={class:"ds-page"},C={class:"ds-card__title"},H={class:"ds-note"},A={class:"ds-card__title"},B={class:"ds-note"},I={class:"ds-card__title"},T={class:"ds-message-stage"},V={class:"ds-card__title"},F={class:"ds-message-stage"},O={class:"ds-card__title"},q={class:"ds-message-stage"},J={class:"ds-card__title"},S={class:"ds-message-stage"},j={class:"ds-note"},L={class:"ds-card__title"},N={class:"ds-message-stage"},R={class:"ds-note"},Y={class:"ds-card__title"},Q={class:"ds-sublabel"},$={class:"ds-sublabel ds-sublabel--gap"},z={class:"ds-note"},P=`<script setup lang="ts">
import MessageContent from '@/components/MessageContent.vue'

// view: { html, text: { forwarded, message, history } } — built by the backend
const view = await fetchMessageView(id)
<\/script>

<template>
  <MessageContent :html="view.html" :text="view.text" />
</template>`,U=`{
  "html": "<p>Hi Anna…</p><details><summary>Quoted history</summary>…</details>",
  "text": {
    "forwarded": "",
    "message": "Hi Anna,\\n\\nThanks for the update…",
    "history": "On Mon, 15 Jun 2026, Anna wrote:\\n…"
  }
}`,D=f({__name:"MessageContentView",setup(E){const{t}=y(),l={html:`<p>Hi Anna,</p><p>Thanks for the update — looks good to me. Let's ship on Friday.</p><p><img src="https://picsum.photos/seed/semaphore/480/120" alt="release banner"></p><p>Best,<br>John</p><details class="mc-spoiler mc-history"><summary></summary><div class="mc-quote"><blockquote>On Mon, 15 Jun 2026, Anna &lt;anna@acme.example&gt; wrote:<br>Here is the latest draft, let me know what you think.</blockquote></div></details>`,text:{forwarded:"",message:`Hi Anna,

Thanks for the update — looks good to me. Let's ship on Friday.

![release banner](https://picsum.photos/seed/semaphore/480/120)

Best,
John`,history:`On Mon, 15 Jun 2026, Anna <anna@acme.example> wrote:
Here is the latest draft, let me know what you think.`}},c={html:'<p>Here is the dashboard you asked about — the new volume chart is live:</p><p><img src="https://picsum.photos/seed/dashboard/520/300" alt="analytics dashboard"></p><p>And a close-up of the filter bar:</p><p><img src="https://picsum.photos/seed/filterbar/360/140" alt="filter bar"></p>',text:{forwarded:"",message:`Here is the dashboard you asked about — the new volume chart is live:

![analytics dashboard](https://picsum.photos/seed/dashboard/520/300)

And a close-up of the filter bar:

![filter bar](https://picsum.photos/seed/filterbar/360/140)`,history:""}},m={html:'<details class="mc-spoiler mc-forwarded"><summary></summary><div class="mc-quote"><p>From: billing@acme.example<br>Subject: Invoice #2026-05</p><p>Your invoice is attached. Total: €240.</p></div></details><p>FYI — forwarding the invoice for your records.</p>',text:{forwarded:`From: billing@acme.example
Subject: Invoice #2026-05

Your invoice is attached. Total: €240.`,message:"FYI — forwarding the invoice for your records.",history:""}},h={html:`<div style="white-space:pre-wrap">Hello team,

Quick reminder about tomorrow's standup at 10:00.</div><details class="mc-spoiler mc-history"><summary></summary><div class="mc-quote"><div style="white-space:pre-wrap">On Mon, someone wrote:
&gt; Are we still on for the standup?</div></div></details>`,text:{forwarded:"",message:`Hello team,

Quick reminder about tomorrow's standup at 10:00.`,history:`On Mon, someone wrote:
> Are we still on for the standup?`}},p="data:image/svg+xml,"+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4a90d9"><path d="M2 21h4V9H2zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73z"/></svg>'),g={html:`<p><img src="${p}"> Tess Roehrig reacted to your message: looks great!</p>`,text:{forwarded:"",message:`![reaction](${p}) Tess Roehrig reacted to your message: looks great!`,history:""}};return(K,X)=>(x(),w(b,null,{default:n(()=>[s("div",M,[e(k,{title:a(t)("design-system.page.message.title"),description:a(t)("design-system.page.message.description"),"back-to":"/design-system"},null,8,["title","description"]),e(i,{class:"ds-card"},{default:n(()=>[s("h6",C,o(a(t)("design-system.section.message.controls")),1),e(_),s("p",H,o(a(t)("design-system.section.message.note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",A,o(a(t)("design-system.section.message.controls_safe")),1),e(_,{"hide-format":""}),s("p",B,o(a(t)("design-system.section.message.controls_safe_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",I,o(a(t)("design-system.section.message.reply")),1),s("div",T,[e(d,{side:"right",tone:"accent",author:"john@acme.example",time:"14:32"},{default:n(()=>[e(r,{html:l.html,text:l.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",V,o(a(t)("design-system.section.message.forward")),1),s("div",F,[e(d,{side:"left",tone:"surface",author:"me@acme.example",time:"09:10"},{default:n(()=>[e(r,{html:m.html,text:m.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",O,o(a(t)("design-system.section.message.plain")),1),s("div",q,[e(d,{side:"left",tone:"surface",author:"team@acme.example",time:"08:00"},{default:n(()=>[e(r,{html:h.html,text:h.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",J,o(a(t)("design-system.section.message.reaction")),1),s("div",S,[e(d,{side:"left",tone:"surface",author:"tess@acme.example",time:"01:46"},{default:n(()=>[e(r,{html:g.html,text:g.text},null,8,["html","text"])]),_:1})]),s("p",j,o(a(t)("design-system.section.message.reaction_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",L,o(a(t)("design-system.section.message.images")),1),s("div",N,[e(d,{side:"left",tone:"surface",author:"dev@acme.example",time:"16:20"},{default:n(()=>[e(r,{html:c.html,text:c.text},null,8,["html","text"])]),_:1})]),s("p",R,o(a(t)("design-system.section.message.images_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",Y,o(a(t)("design-system.section.message.usage")),1),s("p",Q,o(a(t)("design-system.section.message.example")),1),e(u,{code:P,lang:"vue"}),s("p",$,o(a(t)("design-system.section.message.data")),1),s("p",z,o(a(t)("design-system.section.message.data_note")),1),e(u,{code:U,lang:"json"})]),_:1})])]),_:1}))}}),re=v(D,[["__scopeId","data-v-668a8708"]]);export{re as default};
