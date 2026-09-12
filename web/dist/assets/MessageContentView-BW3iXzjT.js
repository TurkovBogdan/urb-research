import{aX as f,bC as y,aQ as w,bN as n,aP as s,aV as e,bx as a,bv as o,a7 as i,aL as b,bi as x,aK as v}from"./index-CLJuoddt.js";import{P as k}from"./PageHeader-JcMnhVzW.js";import{C as u}from"./CodeBlock-DabO9VKI.js";import{a as _,C as d,M as r}from"./MessageViewControls-CCNkn2Wi.js";import"./SectionHeader-B46UkOhw.js";import"./IconCode-CBQWnMnk.js";import"./IconCopy-BnicxZpY.js";import"./purify.es-DxCUJf2h.js";import"./IconEye-MrS4a9QN.js";import"./IconAlignLeft-Cyi7A0xJ.js";const C={class:"ds-page"},M={class:"ds-card__title"},H={class:"ds-note"},A={class:"ds-card__title"},I={class:"ds-note"},T={class:"ds-card__title"},V={class:"ds-message-stage"},B={class:"ds-card__title"},F={class:"ds-message-stage"},O={class:"ds-card__title"},q={class:"ds-message-stage"},J={class:"ds-card__title"},S={class:"ds-message-stage"},j={class:"ds-note"},L={class:"ds-card__title"},N={class:"ds-message-stage"},Q={class:"ds-note"},R={class:"ds-card__title"},Y={class:"ds-sublabel"},P={class:"ds-sublabel ds-sublabel--gap"},$={class:"ds-note"},z=`<script setup lang="ts">
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
}`,D=f({__name:"MessageContentView",setup(E){const{t}=y(),l={html:`<p>Hi Anna,</p><p>Thanks for the update — looks good to me. Let's ship on Friday.</p><p><img src="https://picsum.photos/seed/release/480/120" alt="release banner"></p><p>Best,<br>John</p><details class="mc-spoiler mc-history"><summary></summary><div class="mc-quote"><blockquote>On Mon, 15 Jun 2026, Anna &lt;anna@acme.example&gt; wrote:<br>Here is the latest draft, let me know what you think.</blockquote></div></details>`,text:{forwarded:"",message:`Hi Anna,

Thanks for the update — looks good to me. Let's ship on Friday.

![release banner](https://picsum.photos/seed/release/480/120)

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
> Are we still on for the standup?`}},p="data:image/svg+xml,"+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4a90d9"><path d="M2 21h4V9H2zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73z"/></svg>'),g={html:`<p><img src="${p}"> Tess Roehrig reacted to your message: looks great!</p>`,text:{forwarded:"",message:`![reaction](${p}) Tess Roehrig reacted to your message: looks great!`,history:""}};return(K,X)=>(x(),w(b,null,{default:n(()=>[s("div",C,[e(k,{title:a(t)("design-system.page.message.title"),description:a(t)("design-system.page.message.description"),"back-to":"/design-system"},null,8,["title","description"]),e(i,{class:"ds-card"},{default:n(()=>[s("h6",M,o(a(t)("design-system.section.message.controls")),1),e(_),s("p",H,o(a(t)("design-system.section.message.note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",A,o(a(t)("design-system.section.message.controls_safe")),1),e(_,{"hide-format":""}),s("p",I,o(a(t)("design-system.section.message.controls_safe_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",T,o(a(t)("design-system.section.message.reply")),1),s("div",V,[e(d,{side:"right",tone:"accent",author:"john@acme.example",time:"14:32"},{default:n(()=>[e(r,{html:l.html,text:l.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",B,o(a(t)("design-system.section.message.forward")),1),s("div",F,[e(d,{side:"left",tone:"surface",author:"me@acme.example",time:"09:10"},{default:n(()=>[e(r,{html:m.html,text:m.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",O,o(a(t)("design-system.section.message.plain")),1),s("div",q,[e(d,{side:"left",tone:"surface",author:"team@acme.example",time:"08:00"},{default:n(()=>[e(r,{html:h.html,text:h.text},null,8,["html","text"])]),_:1})])]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",J,o(a(t)("design-system.section.message.reaction")),1),s("div",S,[e(d,{side:"left",tone:"surface",author:"tess@acme.example",time:"01:46"},{default:n(()=>[e(r,{html:g.html,text:g.text},null,8,["html","text"])]),_:1})]),s("p",j,o(a(t)("design-system.section.message.reaction_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",L,o(a(t)("design-system.section.message.images")),1),s("div",N,[e(d,{side:"left",tone:"surface",author:"dev@acme.example",time:"16:20"},{default:n(()=>[e(r,{html:c.html,text:c.text},null,8,["html","text"])]),_:1})]),s("p",Q,o(a(t)("design-system.section.message.images_note")),1)]),_:1}),e(i,{class:"ds-card"},{default:n(()=>[s("h6",R,o(a(t)("design-system.section.message.usage")),1),s("p",Y,o(a(t)("design-system.section.message.example")),1),e(u,{code:z,lang:"vue"}),s("p",P,o(a(t)("design-system.section.message.data")),1),s("p",$,o(a(t)("design-system.section.message.data_note")),1),e(u,{code:U,lang:"json"})]),_:1})])]),_:1}))}}),de=v(D,[["__scopeId","data-v-a55e4057"]]);export{de as default};
