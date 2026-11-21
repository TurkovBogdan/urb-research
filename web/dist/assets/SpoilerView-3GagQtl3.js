import{aZ as h,bE as V,bn as S,aS as x,bP as l,aR as s,aX as n,bz as o,bx as i,aW as d,aU as C,bq as k,F as w,ag as T,aN as U,bo as c,bk as b,aM as B}from"./index-CnJWcYyq.js";import{P as z}from"./PageHeader-Dksx1iPs.js";import{S as r}from"./Spoiler-CQr0ScAB.js";import{C as N}from"./CodeBlock-eqHTnwo5.js";import"./SectionHeader-CzhT1HEK.js";import"./IconCode-C-ec_W9I.js";import"./IconCopy-CFz-agQ0.js";const O={class:"ds-page"},E={class:"ds-section"},F={class:"mb-3"},I={class:"ds-stack"},P={class:"ds-section"},D={class:"mb-3"},H={class:"ds-card"},M={class:"ds-tag"},$={class:"ds-controls"},j={class:"ds-spec"},q={class:"ds-section"},A={class:"mb-3"},L={class:"ds-stack"},Q={class:"ds-section"},R={class:"mb-3"},W={class:"ds-card"},X={class:"ds-row"},Z={class:"ds-controls"},G={class:"ds-section"},J={class:"mb-3"},K={class:"ds-card"},Y={class:"ds-row"},ss={class:"ds-controls"},es={class:"ds-row"},ts={class:"ds-controls"},os={class:"ds-section"},is={class:"mb-3"},as=`<script setup lang="ts">
import { ref } from 'vue'
import Spoiler from '@/components/Spoiler.vue'

const open = ref(false)
<\/script>

<template>
  <!-- Title + content, default theme -->
  <Spoiler v-model="open" title="Technical details">
    Hidden content goes here.
  </Spoiler>

  <!-- Minimal theme — borderless uppercase label -->
  <Spoiler title="Quoted history" variant="minimal">
    <p>Older messages…</p>
  </Spoiler>

  <!-- Custom title + trailing actions -->
  <Spoiler variant="card">
    <template #title>Attachments</template>
    <template #actions>
      <VChip size="x-small">3</VChip>
    </template>
    <p>Files…</p>
  </Spoiler>

  <!-- Custom header colours: resting (color) + hover (active-color) -->
  <Spoiler
    variant="minimal"
    title="Danger zone"
    color="var(--text-faint)"
    active-color="var(--error)"
  >
    <p>Irreversible actions…</p>
  </Spoiler>
</template>`,ls=h({__name:"SpoilerView",setup(ns){const{t:e}=V(),p=c(!1),m=c(!0),u=c(!1),_=c(!1),v=["default","minimal","card"],g=S(Object.fromEntries(v.map(f=>[f,!1])));return(f,t)=>(b(),x(U,null,{default:l(()=>[s("div",O,[n(z,{title:o(e)("design-system.page.spoiler.title"),description:o(e)("design-system.page.spoiler.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",E,[s("h6",F,i(o(e)("design-system.section.spoiler.basic")),1),s("div",I,[n(r,{modelValue:p.value,"onUpdate:modelValue":t[0]||(t[0]=a=>p.value=a),title:o(e)("design-system.section.spoiler.sample.title")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"]),n(r,{modelValue:m.value,"onUpdate:modelValue":t[1]||(t[1]=a=>m.value=a),title:o(e)("design-system.section.spoiler.sample.openTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])])]),s("section",P,[s("h6",D,i(o(e)("design-system.section.spoiler.variants")),1),s("div",H,[(b(),C(w,null,k(v,a=>s("div",{key:a,class:"ds-row"},[s("span",M,i(a),1),s("div",$,[n(r,{modelValue:g[a],"onUpdate:modelValue":y=>g[a]=y,variant:a,title:o(e)(`design-system.section.spoiler.variantSample.${a}`)},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","onUpdate:modelValue","variant","title"])]),s("span",j,'variant="'+i(a)+'"',1)])),64))])]),s("section",q,[s("h6",A,i(o(e)("design-system.section.spoiler.slots")),1),s("div",L,[n(r,{variant:"card"},{title:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.attachments")),1)]),actions:l(()=>[n(T,{size:"x-small",variant:"tonal"},{default:l(()=>[...t[4]||(t[4]=[d("3",-1)])]),_:1})]),default:l(()=>[d(" "+i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1})])]),s("section",Q,[s("h6",R,i(o(e)("design-system.section.spoiler.states")),1),s("div",W,[s("div",X,[t[5]||(t[5]=s("span",{class:"ds-tag"},"disabled",-1)),s("div",Z,[n(r,{modelValue:u.value,"onUpdate:modelValue":t[2]||(t[2]=a=>u.value=a),disabled:"",title:o(e)("design-system.section.spoiler.sample.disabledTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),t[6]||(t[6]=s("span",{class:"ds-spec"},"disabled",-1))])])]),s("section",G,[s("h6",J,i(o(e)("design-system.section.spoiler.colors")),1),s("div",K,[s("div",Y,[t[7]||(t[7]=s("span",{class:"ds-tag"},"accent",-1)),s("div",ss,[n(r,{modelValue:_.value,"onUpdate:modelValue":t[3]||(t[3]=a=>_.value=a),variant:"minimal",color:"var(--text-faint)","active-color":"var(--accent)",title:o(e)("design-system.section.spoiler.sample.colorTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),t[8]||(t[8]=s("span",{class:"ds-spec"},"color / active-color",-1))]),s("div",es,[t[9]||(t[9]=s("span",{class:"ds-tag"},"error",-1)),s("div",ts,[n(r,{variant:"minimal",color:"var(--text-faint)","active-color":"var(--error)",title:o(e)("design-system.section.spoiler.sample.dangerTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["title"])]),t[10]||(t[10]=s("span",{class:"ds-spec"},'active-color="var(--error)"',-1))])])]),s("section",os,[s("h6",is,i(o(e)("design-system.section.spoiler.usage")),1),n(N,{code:as,lang:"vue"})])])]),_:1}))}}),vs=B(ls,[["__scopeId","data-v-dbb4df64"]]);export{vs as default};
