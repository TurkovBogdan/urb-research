import{aV as S,bB as $,aQ as y,aN as s,aT as n,bv as t,o as w,bn as f,aS as d,bt as a,bO as x,aP as T,aj as B,bL as i,bM as I,bI as M,ba as z,b8 as O,b5 as U,aM as N,bg as g,aI as C,bA as j,bj as D,aO as E,bm as F,F as P,ae as A,aJ as H,bk as b}from"./index-DmPD8LZu.js";import{P as L}from"./PageHeader-Bm2NrN2b.js";import{C as Q}from"./CodeBlock-D1gc1QtM.js";import"./SectionHeader-R3U805Ya.js";import"./IconCode-DpyLWJm_.js";import"./IconCopy-Dm2JOzNK.js";const J=["disabled","aria-expanded"],R={class:"spoiler__title"},q={class:"spoiler__body"},G={class:"spoiler__content"},K=S({__name:"Spoiler",props:U({title:{},variant:{default:"default"},disabled:{type:Boolean},color:{},activeColor:{}},{modelValue:{type:Boolean,default:!1},modelModifiers:{}}),emits:["update:modelValue"],setup(c){const e=$(c,"modelValue"),r=c,v=N(()=>({...r.color?{"--spoiler-color":r.color}:{},...r.activeColor?{"--spoiler-active-color":r.activeColor}:{}}));function _(){r.disabled||(e.value=!e.value)}return(p,u)=>(g(),y("div",{class:O(["spoiler",[`spoiler--${c.variant}`,{"spoiler--open":e.value,"spoiler--disabled":c.disabled}]]),style:z(v.value)},[s("button",{type:"button",class:"spoiler__head",disabled:c.disabled,"aria-expanded":e.value,onClick:_},[n(t(w),{class:"spoiler__chevron",size:16,"stroke-width":2}),s("span",R,[f(p.$slots,"title",{},()=>[d(a(c.title),1)],!0)]),p.$slots.actions?(g(),y("span",{key:0,class:"spoiler__actions",onClick:u[0]||(u[0]=x(()=>{},["stop"]))},[f(p.$slots,"actions",{},void 0,!0)])):T("",!0)],8,J),n(B,null,{default:i(()=>[I(s("div",q,[s("div",G,[f(p.$slots,"default",{},void 0,!0)])],512),[[M,e.value]])]),_:3})],6))}}),m=C(K,[["__scopeId","data-v-4b733c22"]]),W={class:"ds-page"},X={class:"ds-section"},Y={class:"mb-3"},Z={class:"ds-stack"},ss={class:"ds-section"},es={class:"mb-3"},ts={class:"ds-card"},os={class:"ds-tag"},as={class:"ds-controls"},ls={class:"ds-spec"},is={class:"ds-section"},ns={class:"mb-3"},ds={class:"ds-stack"},rs={class:"ds-section"},cs={class:"mb-3"},ps={class:"ds-card"},ms={class:"ds-row"},us={class:"ds-controls"},vs={class:"ds-section"},_s={class:"mb-3"},bs={class:"ds-card"},gs={class:"ds-row"},fs={class:"ds-controls"},ys={class:"ds-row"},hs={class:"ds-controls"},Vs={class:"ds-section"},Ss={class:"mb-3"},Cs=`<script setup lang="ts">
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
</template>`,ks=S({__name:"SpoilerView",setup(c){const{t:e}=j(),r=b(!1),v=b(!0),_=b(!1),p=b(!1),u=["default","minimal","card"],h=D(Object.fromEntries(u.map(V=>[V,!1])));return(V,o)=>(g(),E(H,null,{default:i(()=>[s("div",W,[n(L,{title:t(e)("design-system.page.spoiler.title"),description:t(e)("design-system.page.spoiler.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",X,[s("h6",Y,a(t(e)("design-system.section.spoiler.basic")),1),s("div",Z,[n(m,{modelValue:r.value,"onUpdate:modelValue":o[0]||(o[0]=l=>r.value=l),title:t(e)("design-system.section.spoiler.sample.title")},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"]),n(m,{modelValue:v.value,"onUpdate:modelValue":o[1]||(o[1]=l=>v.value=l),title:t(e)("design-system.section.spoiler.sample.openTitle")},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])])]),s("section",ss,[s("h6",es,a(t(e)("design-system.section.spoiler.variants")),1),s("div",ts,[(g(),y(P,null,F(u,l=>s("div",{key:l,class:"ds-row"},[s("span",os,a(l),1),s("div",as,[n(m,{modelValue:h[l],"onUpdate:modelValue":k=>h[l]=k,variant:l,title:t(e)(`design-system.section.spoiler.variantSample.${l}`)},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","onUpdate:modelValue","variant","title"])]),s("span",ls,'variant="'+a(l)+'"',1)])),64))])]),s("section",is,[s("h6",ns,a(t(e)("design-system.section.spoiler.slots")),1),s("div",ds,[n(m,{variant:"card"},{title:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.attachments")),1)]),actions:i(()=>[n(A,{size:"x-small",variant:"tonal"},{default:i(()=>[...o[4]||(o[4]=[d("3",-1)])]),_:1})]),default:i(()=>[d(" "+a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1})])]),s("section",rs,[s("h6",cs,a(t(e)("design-system.section.spoiler.states")),1),s("div",ps,[s("div",ms,[o[5]||(o[5]=s("span",{class:"ds-tag"},"disabled",-1)),s("div",us,[n(m,{modelValue:_.value,"onUpdate:modelValue":o[2]||(o[2]=l=>_.value=l),disabled:"",title:t(e)("design-system.section.spoiler.sample.disabledTitle")},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),o[6]||(o[6]=s("span",{class:"ds-spec"},"disabled",-1))])])]),s("section",vs,[s("h6",_s,a(t(e)("design-system.section.spoiler.colors")),1),s("div",bs,[s("div",gs,[o[7]||(o[7]=s("span",{class:"ds-tag"},"accent",-1)),s("div",fs,[n(m,{modelValue:p.value,"onUpdate:modelValue":o[3]||(o[3]=l=>p.value=l),variant:"minimal",color:"var(--text-faint)","active-color":"var(--accent)",title:t(e)("design-system.section.spoiler.sample.colorTitle")},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["modelValue","title"])]),o[8]||(o[8]=s("span",{class:"ds-spec"},"color / active-color",-1))]),s("div",ys,[o[9]||(o[9]=s("span",{class:"ds-tag"},"error",-1)),s("div",hs,[n(m,{variant:"minimal",color:"var(--text-faint)","active-color":"var(--error)",title:t(e)("design-system.section.spoiler.sample.dangerTitle")},{default:i(()=>[d(a(t(e)("design-system.section.spoiler.sample.body")),1)]),_:1},8,["title"])]),o[10]||(o[10]=s("span",{class:"ds-spec"},'active-color="var(--error)"',-1))])])]),s("section",Vs,[s("h6",Ss,a(t(e)("design-system.section.spoiler.usage")),1),n(Q,{code:Cs,lang:"vue"})])])]),_:1}))}}),Ms=C(ks,[["__scopeId","data-v-dbb4df64"]]);export{Ms as default};
