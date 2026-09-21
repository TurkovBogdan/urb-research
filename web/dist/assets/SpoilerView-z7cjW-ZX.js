import{aY as h,bD as V,bm as S,aR as C,bO as l,aQ as s,aW as n,by as o,bw as i,aV as d,aT as x,bp as k,F as w,af as T,aM as U,bn as c,bj as b,aL as B}from"./index-BILydIpo.js";import{P as O}from"./PageHeader-BFL1BX05.js";import{S as r}from"./Spoiler-BjGTFYhP.js";import{C as z}from"./CodeBlock-hnsNfpTc.js";import"./SectionHeader-DEOOwyp6.js";import"./IconCode-DQ-P6X-2.js";import"./IconCopy-C3hyukUs.js";const D={class:"ds-page"},F={class:"ds-section"},I={class:"mb-3"},N={class:"ds-stack"},j={class:"ds-section"},E={class:"mb-3"},H={class:"ds-card"},L={class:"ds-tag"},M={class:"ds-controls"},P={class:"ds-spec"},Q={class:"ds-section"},$={class:"mb-3"},A={class:"ds-stack"},R={class:"ds-section"},W={class:"mb-3"},Y={class:"ds-card"},q={class:"ds-row"},G={class:"ds-controls"},J={class:"ds-section"},K={class:"mb-3"},X={class:"ds-card"},Z={class:"ds-row"},ss={class:"ds-controls"},es={class:"ds-row"},ts={class:"ds-controls"},os={class:"ds-section"},is={class:"mb-3"},as=`<script setup lang="ts">
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
</template>`,ls=h({__name:"SpoilerView",setup(ns){const{t:e}=V(),p=c(!1),m=c(!0),u=c(!1),_=c(!1),v=["default","minimal","card"],g=S(Object.fromEntries(v.map(f=>[f,!1])));return(f,t)=>(b(),C(U,null,{default:l(()=>[s("div",D,[n(O,{title:o(e)("design-system.page.spoiler.title"),description:o(e)("design-system.page.spoiler.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",F,[s("h6",I,i(o(e)("design-system.section.spoiler.basic")),1),s("div",N,[n(r,{modelValue:p.value,"onUpdate:modelValue":t[0]||(t[0]=a=>p.value=a),title:o(e)("design-system.section.spoiler.sample.title")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"]),n(r,{modelValue:m.value,"onUpdate:modelValue":t[1]||(t[1]=a=>m.value=a),title:o(e)("design-system.section.spoiler.sample.openTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])])]),s("section",j,[s("h6",E,i(o(e)("design-system.section.spoiler.variants")),1),s("div",H,[(b(),x(w,null,k(v,a=>s("div",{key:a,class:"ds-row"},[s("span",L,i(a),1),s("div",M,[n(r,{modelValue:g[a],"onUpdate:modelValue":y=>g[a]=y,variant:a,title:o(e)(`design-system.section.spoiler.variantSample.${a}`)},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","onUpdate:modelValue","variant","title"])]),s("span",P,'variant="'+i(a)+'"',1)])),64))])]),s("section",Q,[s("h6",$,i(o(e)("design-system.section.spoiler.slots")),1),s("div",A,[n(r,{variant:"card"},{title:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.attachments")),1)]),actions:l(()=>[n(T,{size:"x-small",variant:"tonal"},{default:l(()=>[...t[4]||(t[4]=[d("3",-1)])]),_:1})]),default:l(()=>[d(" "+i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1})])]),s("section",R,[s("h6",W,i(o(e)("design-system.section.spoiler.states")),1),s("div",Y,[s("div",q,[t[5]||(t[5]=s("span",{class:"ds-tag"},"disabled",-1)),s("div",G,[n(r,{modelValue:u.value,"onUpdate:modelValue":t[2]||(t[2]=a=>u.value=a),disabled:"",title:o(e)("design-system.section.spoiler.sample.disabledTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),t[6]||(t[6]=s("span",{class:"ds-spec"},"disabled",-1))])])]),s("section",J,[s("h6",K,i(o(e)("design-system.section.spoiler.colors")),1),s("div",X,[s("div",Z,[t[7]||(t[7]=s("span",{class:"ds-tag"},"accent",-1)),s("div",ss,[n(r,{modelValue:_.value,"onUpdate:modelValue":t[3]||(t[3]=a=>_.value=a),variant:"minimal",color:"var(--text-faint)","active-color":"var(--accent)",title:o(e)("design-system.section.spoiler.sample.colorTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),t[8]||(t[8]=s("span",{class:"ds-spec"},"color / active-color",-1))]),s("div",es,[t[9]||(t[9]=s("span",{class:"ds-tag"},"error",-1)),s("div",ts,[n(r,{variant:"minimal",color:"var(--text-faint)","active-color":"var(--error)",title:o(e)("design-system.section.spoiler.sample.dangerTitle")},{default:l(()=>[d(i(o(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["title"])]),t[10]||(t[10]=s("span",{class:"ds-spec"},'active-color="var(--error)"',-1))])])]),s("section",os,[s("h6",is,i(o(e)("design-system.section.spoiler.usage")),1),n(z,{code:as,lang:"vue"})])])]),_:1}))}}),vs=B(ls,[["__scopeId","data-v-dbb4df64"]]);export{vs as default};
