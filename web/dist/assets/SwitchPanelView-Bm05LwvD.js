import{aI as P,be as U,a$ as b,aB as k,bo as V,aA as s,aG as l,bb as i,b9 as n,aF as D,aD as S,b2 as T,F as x,aw as O,b0 as d,aZ as r,av as B}from"./index-Ck6Fpicj.js";import{P as C}from"./PageHeader-tc2LA7XG.js";import{S as a}from"./SwitchPanel-Dtpllgiz.js";import{C as E}from"./CodeBlock-Mnz8eEBw.js";import"./IconCode-DQa8dIfp.js";import"./IconCopy-CnfBC-II.js";const I={class:"ds-page"},N={class:"ds-section"},$={class:"mb-3"},j={class:"ds-card"},F={class:"ds-row"},H={class:"ds-controls"},z={class:"ds-row"},A={class:"ds-controls"},G={class:"ds-row"},L={class:"ds-controls"},M={class:"ds-section"},Z={class:"mb-3"},q={class:"ds-card"},J={class:"ds-row"},K={class:"ds-controls"},Q={class:"ds-section"},R={class:"mb-3"},W={class:"ds-card"},X={class:"ds-tag"},Y={class:"ds-controls"},ss={class:"ds-spec"},es={class:"ds-section"},ts={class:"mb-3"},os={class:"ds-card"},is={class:"ds-tag"},ns={class:"ds-controls"},ls={class:"ds-spec"},as={class:"ds-section"},ds={class:"mb-3"},cs={class:"ds-card"},ps={class:"ds-row"},rs={class:"ds-controls"},ms={class:"ds-section"},us={class:"mb-3"},hs=`<script setup lang="ts">
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
</template>`,ws=P({__name:"SwitchPanelView",setup(fs){const{t:o}=U(),m=d(!0),u=d(!1),h=d(!0),w=d(!1),f=d(!0),_=["default","primary","info","success","warning","error","transparent"],v=b(Object.fromEntries(_.map(c=>[c,!0]))),g=["primary","info","success","warning","error"],y=b(Object.fromEntries(g.map(c=>[c,!0])));return(c,e)=>(r(),k(O,null,{default:V(()=>[s("div",I,[l(C,{title:i(o)("design-system.page.switch-panel.title"),description:i(o)("design-system.page.switch-panel.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",N,[s("h6",$,n(i(o)("design-system.section.switch-panel.basic")),1),s("div",j,[s("div",F,[e[5]||(e[5]=s("span",{class:"ds-tag"},"title + desc",-1)),s("div",H,[l(a,{modelValue:u.value,"onUpdate:modelValue":e[0]||(e[0]=t=>u.value=t),title:i(o)("design-system.section.switch-panel.sample.title"),description:i(o)("design-system.section.switch-panel.sample.desc")},null,8,["modelValue","title","description"])]),e[6]||(e[6]=s("span",{class:"ds-spec"},"v-model · title · description",-1))]),s("div",z,[e[7]||(e[7]=s("span",{class:"ds-tag"},"title only",-1)),s("div",A,[l(a,{modelValue:h.value,"onUpdate:modelValue":e[1]||(e[1]=t=>h.value=t),title:i(o)("design-system.section.switch-panel.sample.activeTitle")},null,8,["modelValue","title"])]),e[8]||(e[8]=s("span",{class:"ds-spec"},"title",-1))]),s("div",G,[e[9]||(e[9]=s("span",{class:"ds-tag"},"slot",-1)),s("div",L,[l(a,{modelValue:m.value,"onUpdate:modelValue":e[2]||(e[2]=t=>m.value=t)},{default:V(()=>[D(n(i(o)("design-system.section.switch-panel.sample.slot")),1)]),_:1},8,["modelValue"])]),e[10]||(e[10]=s("span",{class:"ds-spec"},"default slot — rich text",-1))])])]),s("section",M,[s("h6",Z,n(i(o)("design-system.section.switch-panel.stateText")),1),s("div",q,[s("div",J,[e[11]||(e[11]=s("span",{class:"ds-tag"},"on / off",-1)),s("div",K,[l(a,{modelValue:w.value,"onUpdate:modelValue":e[3]||(e[3]=t=>w.value=t),"title-on":i(o)("design-system.section.switch-panel.sample.onTitle"),"title-off":i(o)("design-system.section.switch-panel.sample.offTitle"),"description-on":i(o)("design-system.section.switch-panel.sample.onDesc"),"description-off":i(o)("design-system.section.switch-panel.sample.offDesc")},null,8,["modelValue","title-on","title-off","description-on","description-off"])]),e[12]||(e[12]=s("span",{class:"ds-spec"},"titleOn/Off · descriptionOn/Off",-1))])])]),s("section",Q,[s("h6",R,n(i(o)("design-system.section.switch-panel.tones")),1),s("div",W,[(r(),S(x,null,T(_,t=>s("div",{key:t,class:"ds-row"},[s("span",X,n(t),1),s("div",Y,[l(a,{modelValue:v[t],"onUpdate:modelValue":p=>v[t]=p,tone:t,title:i(o)(`design-system.section.switch-panel.toneSample.${t}`),description:i(o)("design-system.section.switch-panel.toneDesc")},null,8,["modelValue","onUpdate:modelValue","tone","title","description"])]),s("span",ss,'tone="'+n(t)+'"',1)])),64))])]),s("section",es,[s("h6",ts,n(i(o)("design-system.section.switch-panel.switchTone")),1),s("div",os,[(r(),S(x,null,T(g,t=>s("div",{key:t,class:"ds-row"},[s("span",is,n(t),1),s("div",ns,[l(a,{modelValue:y[t],"onUpdate:modelValue":p=>y[t]=p,"switch-tone":t,title:i(o)(`design-system.section.switch-panel.toneSample.${t}`),description:i(o)("design-system.section.switch-panel.switchToneDesc")},null,8,["modelValue","onUpdate:modelValue","switch-tone","title","description"])]),s("span",ls,'switch-tone="'+n(t)+'"',1)])),64))])]),s("section",as,[s("h6",ds,n(i(o)("design-system.section.switch-panel.states")),1),s("div",cs,[s("div",ps,[e[13]||(e[13]=s("span",{class:"ds-tag"},"disabled",-1)),s("div",rs,[l(a,{modelValue:f.value,"onUpdate:modelValue":e[4]||(e[4]=t=>f.value=t),disabled:"",title:i(o)("design-system.section.switch-panel.sample.disabledTitle"),description:i(o)("design-system.section.switch-panel.sample.disabledDesc")},null,8,["modelValue","title","description"])]),e[14]||(e[14]=s("span",{class:"ds-spec"},"disabled",-1))])])]),s("section",ms,[s("h6",us,n(i(o)("design-system.section.switch-panel.usage")),1),l(E,{code:hs,lang:"vue"})])])]),_:1}))}}),Ss=B(ws,[["__scopeId","data-v-a51b5593"]]);export{Ss as default};
