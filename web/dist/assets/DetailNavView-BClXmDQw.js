import{aX as l,bC as c,aQ as p,bN as i,aP as s,aV as n,bx as t,bv as o,an as m,ap as _,aU as v,aL as h,bi as g,aK as u}from"./index-eEVCSVbQ.js";import{I as y}from"./IconFolderPlus-aIr7AIyi.js";import{P as f}from"./PageHeader-Dm7m5lo7.js";import{D as b}from"./DetailNav-DD7UWjFw.js";import{D}from"./DetailHead-DkupKB0z.js";import{C as d}from"./CodeBlock-DdYIEENs.js";import"./SectionHeader-D2c4aH42.js";import"./IconCopy-CVWY0q3M.js";import"./IconSettings-DQ9bq44W.js";import"./useClipboard-CSUp9jIN.js";import"./SwitchPanel-Dl_ZCTVn.js";import"./VSelectStepper-DfjBhJWk.js";import"./IconDotsVertical-CtF9l4jQ.js";import"./CopyCodeButton-XMPVxCLI.js";import"./IconCode-DPglK9cv.js";const w={class:"ds-page"},V={class:"ds-section"},C={class:"mb-3"},P={class:"ds-note"},x={class:"ds-section"},E={class:"mb-3"},N={class:"ds-note"},S={class:"ds-frame ds-rail"},k={class:"ds-section"},H={class:"mb-3"},L={class:"ds-note"},A={class:"ds-frame"},I={class:"ds-shelf"},R={class:"ds-title"},T={class:"ds-section"},B={class:"mb-3"},q={class:"ds-card"},M={class:"ds-row"},$={class:"ds-part"},F={class:"ds-row"},G={class:"ds-part"},K={class:"ds-row"},O={class:"ds-part"},Q={class:"ds-row"},U={class:"ds-part"},X={class:"ds-row"},j={class:"ds-part"},z={class:"ds-row"},J={class:"ds-part"},W={class:"ds-row"},Y={class:"ds-part"},Z={class:"ds-row"},ss={class:"ds-part"},es={class:"ds-section"},ts={class:"mb-3"},r="RESEARCH@bc854947af58733bd93c3d",as=`// routes.ts — деталки дети общей рамки
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
</template>`,ns="const parentPath = computed(() =>\n  source.value ? `/research/areas/${source.value.area_code}` : '/research/researches',\n)",is="/design-system/detail-nav",ds=l({__name:"DetailNavView",setup(rs){const{t:a}=c();return(ls,e)=>(g(),p(h,null,{default:i(()=>[s("div",w,[n(f,{title:t(a)("design-system.page.detail-nav.title"),description:t(a)("design-system.page.detail-nav.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",V,[s("h6",C,o(t(a)("design-system.section.detail-nav.rule")),1),s("p",P,o(t(a)("design-system.section.detail-nav.rule_note")),1)]),s("section",x,[s("h6",E,o(t(a)("design-system.section.detail-nav.panel")),1),s("p",N,o(t(a)("design-system.section.detail-nav.panel_note")),1),s("div",S,[n(b,{parent:is,label:t(a)("design-system.section.detail-nav.sample.exit"),code:r,appearance:""},null,8,["label"])]),n(d,{code:ns,lang:"ts"})]),s("section",k,[s("h6",H,o(t(a)("design-system.section.detail-nav.head")),1),s("p",L,o(t(a)("design-system.section.detail-nav.head_note")),1),s("div",A,[n(D,{code:r},{more:i(()=>[n(m,{"prepend-icon":t(y)},{default:i(()=>[n(_,null,{default:i(()=>[v(o(t(a)("design-system.section.detail-nav.sample.move_group")),1)]),_:1})]),_:1},8,["prepend-icon"])]),above:i(()=>[s("span",I,o(t(a)("design-system.section.detail-nav.sample.shelf")),1)]),default:i(()=>[s("h1",R,o(t(a)("design-system.section.detail-nav.sample.title")),1)]),_:1})])]),s("section",T,[s("h6",B,o(t(a)("design-system.section.detail-nav.parts")),1),s("div",q,[s("div",M,[e[0]||(e[0]=s("span",{class:"ds-tag"},"DetailLayout",-1)),s("p",$,o(t(a)("design-system.section.detail-nav.part.layout")),1),e[1]||(e[1]=s("span",{class:"ds-spec"},"320px + minmax(0, 1fr)",-1))]),s("div",F,[e[2]||(e[2]=s("span",{class:"ds-tag"},"назад",-1)),s("p",G,o(t(a)("design-system.section.detail-nav.part.back")),1),e[3]||(e[3]=s("span",{class:"ds-spec"},"история → parent",-1))]),s("div",K,[e[4]||(e[4]=s("span",{class:"ds-tag"},"оформление",-1)),s("p",O,o(t(a)("design-system.section.detail-nav.part.appearance")),1),e[5]||(e[5]=s("span",{class:"ds-spec"},"карточка под панелью",-1))]),s("div",Q,[e[6]||(e[6]=s("span",{class:"ds-tag"},"parent",-1)),s("p",U,o(t(a)("design-system.section.detail-nav.part.parent")),1),e[7]||(e[7]=s("span",{class:"ds-spec"},"один уровень вверх",-1))]),s("div",X,[e[8]||(e[8]=s("span",{class:"ds-tag"},"code",-1)),s("p",j,o(t(a)("design-system.section.detail-nav.part.code")),1),e[9]||(e[9]=s("span",{class:"ds-spec"},"шапка + колонка",-1))]),s("div",z,[e[10]||(e[10]=s("span",{class:"ds-tag"},"DetailHead",-1)),s("p",J,o(t(a)("design-system.section.detail-nav.part.head")),1),e[11]||(e[11]=s("span",{class:"ds-spec"},"надпись над карточками",-1))]),s("div",W,[e[12]||(e[12]=s("span",{class:"ds-tag"},"обновить",-1)),s("p",Y,o(t(a)("design-system.section.detail-nav.part.refresh")),1),e[13]||(e[13]=s("span",{class:"ds-spec"},"правый край первой строки",-1))]),s("div",Z,[e[14]||(e[14]=s("span",{class:"ds-tag"},"more",-1)),s("p",ss,o(t(a)("design-system.section.detail-nav.part.more")),1),e[15]||(e[15]=s("span",{class:"ds-spec"},"слот, иначе кнопки нет",-1))])])]),s("section",es,[s("h6",ts,o(t(a)("design-system.section.detail-nav.markup")),1),n(d,{code:as,lang:"ts"}),n(d,{code:os,lang:"vue"})])])]),_:1}))}}),Ps=u(ds,[["__scopeId","data-v-64427ecf"]]);export{Ps as default};
