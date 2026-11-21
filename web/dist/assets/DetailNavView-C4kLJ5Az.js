import{aZ as l,bE as c,aS as p,bP as i,aR as s,aX as n,bz as t,bx as o,ap as m,ar as _,aW as v,aN as h,bk as g,aM as u}from"./index-CnJWcYyq.js";import{I as y}from"./IconFolderPlus-BvSue56a.js";import{P as f}from"./PageHeader-Dksx1iPs.js";import{D as b}from"./DetailNav-D3R6eRXk.js";import{D}from"./DetailHead-D9kOFlCe.js";import{C as d}from"./CodeBlock-eqHTnwo5.js";import"./SectionHeader-CzhT1HEK.js";import"./IconCopy-CFz-agQ0.js";import"./IconSettings-CASu6U8I.js";import"./useClipboard-BpCrxIkS.js";import"./SwitchPanel-3fQNc5HF.js";import"./VSelectStepper-Ci6Rs7B3.js";import"./IconDotsVertical-DjDvtKyj.js";import"./CopyCodeButton-BE72d-xH.js";import"./IconCode-C-ec_W9I.js";const w={class:"ds-page"},E={class:"ds-section"},P={class:"mb-3"},S={class:"ds-note"},V={class:"ds-section"},k={class:"mb-3"},x={class:"ds-note"},C={class:"ds-frame ds-rail"},N={class:"ds-section"},H={class:"mb-3"},R={class:"ds-note"},A={class:"ds-frame"},I={class:"ds-shelf"},L={class:"ds-title"},T={class:"ds-section"},B={class:"mb-3"},M={class:"ds-card"},q={class:"ds-row"},$={class:"ds-part"},z={class:"ds-row"},F={class:"ds-part"},G={class:"ds-row"},O={class:"ds-part"},W={class:"ds-row"},X={class:"ds-part"},Z={class:"ds-row"},j={class:"ds-part"},J={class:"ds-row"},K={class:"ds-part"},Q={class:"ds-row"},U={class:"ds-part"},Y={class:"ds-row"},ss={class:"ds-part"},es={class:"ds-section"},ts={class:"mb-3"},r="RESEARCH@bc854947af58733bd93c3d",as=`// routes.ts — деталки дети общей рамки
{
  path: '/research',
  component: () => import('@/layout/templates/DetailShell.vue'),
  children: [
    { path: 'researches/:code', name: 'research-detail', component: … },
    { path: 'areas/:code',      name: 'research-area',   component: … },
  ],
}

// ResearchView.vue
useDetailRail(() => ({
  parent: PARENT_PATH,
  label: t('research.back.researches'),
  code: store.research?.code ?? '',
  appearance: true,
  sections: navSections.value,
  search: {
    label: t('research.research.detail.search'),
    value: store.search,
    update: (query) => { store.search = query },
    summary: store.searching ? t('research.research.detail.found', { n: store.matchCount }) : '',
  },
}))`,os=`<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <!-- Имя артефакта принадлежит артефакту, поэтому стоит над содержимым, а не в колонке.
         Действия — у правого края этой же строки, на всех деталках в одном месте. -->
    <DetailHead :code="store.research.code" :loading="store.loading" @refresh="reload">
      <template #above><GroupLink v-bind="shelf" /></template>
      <TitleEditor variant="title" :heading="1" :title="store.research.title" … />
    </DetailHead>

    <VCard variant="outlined" rounded="lg">…</VCard>
  </div>
</template>`,ns="const parentPath = computed(() =>\n  source.value ? `/research/areas/${source.value.area_code}` : '/research/researches',\n)",is="/design-system/detail-nav",ds=l({__name:"DetailNavView",setup(rs){const{t:a}=c();return(ls,e)=>(g(),p(h,null,{default:i(()=>[s("div",w,[n(f,{title:t(a)("design-system.page.detail-nav.title"),description:t(a)("design-system.page.detail-nav.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",E,[s("h6",P,o(t(a)("design-system.section.detail-nav.rule")),1),s("p",S,o(t(a)("design-system.section.detail-nav.rule_note")),1)]),s("section",V,[s("h6",k,o(t(a)("design-system.section.detail-nav.panel")),1),s("p",x,o(t(a)("design-system.section.detail-nav.panel_note")),1),s("div",C,[n(b,{parent:is,label:t(a)("design-system.section.detail-nav.sample.exit"),code:r,appearance:""},null,8,["label"])]),n(d,{code:ns,lang:"ts"})]),s("section",N,[s("h6",H,o(t(a)("design-system.section.detail-nav.head")),1),s("p",R,o(t(a)("design-system.section.detail-nav.head_note")),1),s("div",A,[n(D,{code:r},{more:i(()=>[n(m,{"prepend-icon":t(y)},{default:i(()=>[n(_,null,{default:i(()=>[v(o(t(a)("design-system.section.detail-nav.sample.move_group")),1)]),_:1})]),_:1},8,["prepend-icon"])]),above:i(()=>[s("span",I,o(t(a)("design-system.section.detail-nav.sample.shelf")),1)]),default:i(()=>[s("h1",L,o(t(a)("design-system.section.detail-nav.sample.title")),1)]),_:1})])]),s("section",T,[s("h6",B,o(t(a)("design-system.section.detail-nav.parts")),1),s("div",M,[s("div",q,[e[0]||(e[0]=s("span",{class:"ds-tag"},"DetailLayout",-1)),s("p",$,o(t(a)("design-system.section.detail-nav.part.layout")),1),e[1]||(e[1]=s("span",{class:"ds-spec"},"320px + minmax(0, 1fr)",-1))]),s("div",z,[e[2]||(e[2]=s("span",{class:"ds-tag"},"назад",-1)),s("p",F,o(t(a)("design-system.section.detail-nav.part.back")),1),e[3]||(e[3]=s("span",{class:"ds-spec"},"история → parent",-1))]),s("div",G,[e[4]||(e[4]=s("span",{class:"ds-tag"},"оформление",-1)),s("p",O,o(t(a)("design-system.section.detail-nav.part.appearance")),1),e[5]||(e[5]=s("span",{class:"ds-spec"},"карточка под панелью",-1))]),s("div",W,[e[6]||(e[6]=s("span",{class:"ds-tag"},"parent",-1)),s("p",X,o(t(a)("design-system.section.detail-nav.part.parent")),1),e[7]||(e[7]=s("span",{class:"ds-spec"},"один уровень вверх",-1))]),s("div",Z,[e[8]||(e[8]=s("span",{class:"ds-tag"},"code",-1)),s("p",j,o(t(a)("design-system.section.detail-nav.part.code")),1),e[9]||(e[9]=s("span",{class:"ds-spec"},"шапка + колонка",-1))]),s("div",J,[e[10]||(e[10]=s("span",{class:"ds-tag"},"DetailHead",-1)),s("p",K,o(t(a)("design-system.section.detail-nav.part.head")),1),e[11]||(e[11]=s("span",{class:"ds-spec"},"надпись над карточками",-1))]),s("div",Q,[e[12]||(e[12]=s("span",{class:"ds-tag"},"обновить",-1)),s("p",U,o(t(a)("design-system.section.detail-nav.part.refresh")),1),e[13]||(e[13]=s("span",{class:"ds-spec"},"правый край первой строки",-1))]),s("div",Y,[e[14]||(e[14]=s("span",{class:"ds-tag"},"more",-1)),s("p",ss,o(t(a)("design-system.section.detail-nav.part.more")),1),e[15]||(e[15]=s("span",{class:"ds-spec"},"слот, иначе кнопки нет",-1))])])]),s("section",es,[s("h6",ts,o(t(a)("design-system.section.detail-nav.markup")),1),n(d,{code:as,lang:"ts"}),n(d,{code:os,lang:"vue"})])])]),_:1}))}}),Ss=u(ds,[["__scopeId","data-v-64427ecf"]]);export{Ss as default};
