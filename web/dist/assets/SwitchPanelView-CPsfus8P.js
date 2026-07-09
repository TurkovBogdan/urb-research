import{ak as P,aN as k,aC as V,ad as U,aX as b,ac as s,ai as l,aL as i,aK as n,ah as D,af as S,aE as T,F as x,aD as d,aB as r,aa as O}from"./index-DucitkGq.js";import{_ as C}from"./PageLayout.vue_vue_type_script_setup_true_lang-BWR86Zx6.js";import{P as E}from"./PageHeader-BYf4O_Bt.js";import{S as a}from"./SwitchPanel-qA-vSWsm.js";import{C as B}from"./CodeBlock-DCPeG-aC.js";import"./IconArrowLeft-D6XlGFor.js";import"./IconCode-kIIWdYAh.js";const N={class:"ds-page"},I={class:"ds-section"},j={class:"mb-3"},$={class:"ds-card"},F={class:"ds-row"},H={class:"ds-controls"},L={class:"ds-row"},z={class:"ds-controls"},K={class:"ds-row"},M={class:"ds-controls"},X={class:"ds-section"},q={class:"mb-3"},A={class:"ds-card"},G={class:"ds-row"},J={class:"ds-controls"},Q={class:"ds-section"},R={class:"mb-3"},W={class:"ds-card"},Y={class:"ds-tag"},Z={class:"ds-controls"},ss={class:"ds-spec"},es={class:"ds-section"},ts={class:"mb-3"},os={class:"ds-card"},is={class:"ds-tag"},ns={class:"ds-controls"},ls={class:"ds-spec"},as={class:"ds-section"},ds={class:"mb-3"},cs={class:"ds-card"},ps={class:"ds-row"},rs={class:"ds-controls"},ms={class:"ds-section"},us={class:"mb-3"},hs=`<script setup lang="ts">
import { ref } from 'vue'
import SwitchPanel from '@/components/SwitchPanel.vue'

const active = ref(true)
const paused = ref(false)
<\/script>

<template>
  <!-- Common title + description -->
  <SwitchPanel
    v-model="active"
    title="Mailbox active"
    description="Email import is enabled."
  />

  <!-- Separate text for the on / off state -->
  <SwitchPanel
    v-model="paused"
    title-on="Import enabled"
    title-off="Import disabled"
    description-on="Emails are synced on schedule."
    description-off="Synchronization is paused."
  />

  <!-- Semantic tone — changes the panel background and the switch color -->
  <SwitchPanel
    v-model="active"
    tone="warning"
    title="Heads up"
    description="This action affects every mailbox."
  />

  <!-- Neutral panel, coloured switch only — switchTone overrides just the switch -->
  <SwitchPanel
    v-model="paused"
    switch-tone="error"
    title="Exclude from processing"
    description="The item won't be processed."
  />
</template>`,ws=P({__name:"SwitchPanelView",setup(fs){const{t:o}=k(),m=d(!0),u=d(!1),h=d(!0),w=d(!1),f=d(!0),_=["default","primary","info","success","warning","error","transparent"],v=V(Object.fromEntries(_.map(c=>[c,!0]))),g=["primary","info","success","warning","error"],y=V(Object.fromEntries(g.map(c=>[c,!0])));return(c,e)=>(r(),U(C,null,{default:b(()=>[s("div",N,[l(E,{title:i(o)("design-system.page.switch-panel.title"),description:i(o)("design-system.page.switch-panel.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",I,[s("h6",j,n(i(o)("design-system.section.switch-panel.basic")),1),s("div",$,[s("div",F,[e[5]||(e[5]=s("span",{class:"ds-tag"},"title + desc",-1)),s("div",H,[l(a,{modelValue:u.value,"onUpdate:modelValue":e[0]||(e[0]=t=>u.value=t),title:i(o)("design-system.section.switch-panel.sample.title"),description:i(o)("design-system.section.switch-panel.sample.desc")},null,8,["modelValue","title","description"])]),e[6]||(e[6]=s("span",{class:"ds-spec"},"v-model · title · description",-1))]),s("div",L,[e[7]||(e[7]=s("span",{class:"ds-tag"},"title only",-1)),s("div",z,[l(a,{modelValue:h.value,"onUpdate:modelValue":e[1]||(e[1]=t=>h.value=t),title:i(o)("design-system.section.switch-panel.sample.activeTitle")},null,8,["modelValue","title"])]),e[8]||(e[8]=s("span",{class:"ds-spec"},"title",-1))]),s("div",K,[e[9]||(e[9]=s("span",{class:"ds-tag"},"slot",-1)),s("div",M,[l(a,{modelValue:m.value,"onUpdate:modelValue":e[2]||(e[2]=t=>m.value=t)},{default:b(()=>[D(n(i(o)("design-system.section.switch-panel.sample.slot")),1)]),_:1},8,["modelValue"])]),e[10]||(e[10]=s("span",{class:"ds-spec"},"default slot — rich text",-1))])])]),s("section",X,[s("h6",q,n(i(o)("design-system.section.switch-panel.stateText")),1),s("div",A,[s("div",G,[e[11]||(e[11]=s("span",{class:"ds-tag"},"on / off",-1)),s("div",J,[l(a,{modelValue:w.value,"onUpdate:modelValue":e[3]||(e[3]=t=>w.value=t),"title-on":i(o)("design-system.section.switch-panel.sample.onTitle"),"title-off":i(o)("design-system.section.switch-panel.sample.offTitle"),"description-on":i(o)("design-system.section.switch-panel.sample.onDesc"),"description-off":i(o)("design-system.section.switch-panel.sample.offDesc")},null,8,["modelValue","title-on","title-off","description-on","description-off"])]),e[12]||(e[12]=s("span",{class:"ds-spec"},"titleOn/Off · descriptionOn/Off",-1))])])]),s("section",Q,[s("h6",R,n(i(o)("design-system.section.switch-panel.tones")),1),s("div",W,[(r(),S(x,null,T(_,t=>s("div",{key:t,class:"ds-row"},[s("span",Y,n(t),1),s("div",Z,[l(a,{modelValue:v[t],"onUpdate:modelValue":p=>v[t]=p,tone:t,title:i(o)(`design-system.section.switch-panel.toneSample.${t}`),description:i(o)("design-system.section.switch-panel.toneDesc")},null,8,["modelValue","onUpdate:modelValue","tone","title","description"])]),s("span",ss,'tone="'+n(t)+'"',1)])),64))])]),s("section",es,[s("h6",ts,n(i(o)("design-system.section.switch-panel.switchTone")),1),s("div",os,[(r(),S(x,null,T(g,t=>s("div",{key:t,class:"ds-row"},[s("span",is,n(t),1),s("div",ns,[l(a,{modelValue:y[t],"onUpdate:modelValue":p=>y[t]=p,"switch-tone":t,title:i(o)(`design-system.section.switch-panel.toneSample.${t}`),description:i(o)("design-system.section.switch-panel.switchToneDesc")},null,8,["modelValue","onUpdate:modelValue","switch-tone","title","description"])]),s("span",ls,'switch-tone="'+n(t)+'"',1)])),64))])]),s("section",as,[s("h6",ds,n(i(o)("design-system.section.switch-panel.states")),1),s("div",cs,[s("div",ps,[e[13]||(e[13]=s("span",{class:"ds-tag"},"disabled",-1)),s("div",rs,[l(a,{modelValue:f.value,"onUpdate:modelValue":e[4]||(e[4]=t=>f.value=t),disabled:"",title:i(o)("design-system.section.switch-panel.sample.disabledTitle"),description:i(o)("design-system.section.switch-panel.sample.disabledDesc")},null,8,["modelValue","title","description"])]),e[14]||(e[14]=s("span",{class:"ds-spec"},"disabled",-1))])])]),s("section",ms,[s("h6",us,n(i(o)("design-system.section.switch-panel.usage")),1),l(B,{code:hs,lang:"vue"})])])]),_:1}))}}),Ts=O(ws,[["__scopeId","data-v-a51b5593"]]);export{Ts as default};
