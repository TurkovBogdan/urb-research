import{aV as l,bA as c,aO as p,bL as d,aN as s,aT as n,bv as t,bt as o,am as m,ao as _,aS as v,aJ as h,bg as g,aI as u}from"./index-DmPD8LZu.js";import{I as y}from"./IconFolderPlus-CZ3xZBF1.js";import{P as f}from"./PageHeader-Bm2NrN2b.js";import{D as b}from"./DetailNav-DOu5Xb9z.js";import{D}from"./DetailHead-Do2GngYx.js";import{C as i}from"./CodeBlock-D1gc1QtM.js";import"./SectionHeader-R3U805Ya.js";import"./IconCopy-Dm2JOzNK.js";import"./IconSettings-OqNQ_kso.js";import"./useClipboard-BdmdtL9W.js";import"./IconDotsVertical-BXjbOdjk.js";import"./CopyCodeButton-BBwHvCPV.js";import"./IconCode-DpyLWJm_.js";const w={class:"ds-page"},V={class:"ds-section"},S={class:"mb-3"},C={class:"ds-note"},E={class:"ds-section"},N={class:"mb-3"},P={class:"ds-note"},k={class:"ds-frame ds-rail"},x={class:"ds-section"},A={class:"mb-3"},H={class:"ds-note"},I={class:"ds-frame"},L={class:"ds-shelf"},T={class:"ds-title"},R={class:"ds-section"},B={class:"mb-3"},q={class:"ds-card"},M={class:"ds-row"},O={class:"ds-part"},$={class:"ds-row"},F={class:"ds-part"},G={class:"ds-row"},J={class:"ds-part"},j={class:"ds-row"},z={class:"ds-part"},K={class:"ds-row"},Q={class:"ds-part"},U={class:"ds-row"},W={class:"ds-part"},X={class:"ds-row"},Y={class:"ds-part"},Z={class:"ds-row"},ss={class:"ds-part"},es={class:"ds-section"},ts={class:"mb-3"},r="RESEARCH@bc854947af58733bd93c3d",as=`// routes.ts — деталки дети общей рамки
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
</template>`,ns="const parentPath = computed(() =>\n  source.value ? `/research/areas/${source.value.area_code}` : '/research/researches',\n)",ds="/design-system/detail-nav",is=l({__name:"DetailNavView",setup(rs){const{t:a}=c();return(ls,e)=>(g(),p(h,null,{default:d(()=>[s("div",w,[n(f,{title:t(a)("design-system.page.detail-nav.title"),description:t(a)("design-system.page.detail-nav.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",V,[s("h6",S,o(t(a)("design-system.section.detail-nav.rule")),1),s("p",C,o(t(a)("design-system.section.detail-nav.rule_note")),1)]),s("section",E,[s("h6",N,o(t(a)("design-system.section.detail-nav.panel")),1),s("p",P,o(t(a)("design-system.section.detail-nav.panel_note")),1),s("div",k,[n(b,{parent:ds,label:t(a)("design-system.section.detail-nav.sample.exit"),code:r,appearance:""},null,8,["label"])]),n(i,{code:ns,lang:"ts"})]),s("section",x,[s("h6",A,o(t(a)("design-system.section.detail-nav.head")),1),s("p",H,o(t(a)("design-system.section.detail-nav.head_note")),1),s("div",I,[n(D,{code:r},{more:d(()=>[n(m,{"prepend-icon":t(y)},{default:d(()=>[n(_,null,{default:d(()=>[v(o(t(a)("design-system.section.detail-nav.sample.move_group")),1)]),_:1})]),_:1},8,["prepend-icon"])]),above:d(()=>[s("span",L,o(t(a)("design-system.section.detail-nav.sample.shelf")),1)]),default:d(()=>[s("h1",T,o(t(a)("design-system.section.detail-nav.sample.title")),1)]),_:1})])]),s("section",R,[s("h6",B,o(t(a)("design-system.section.detail-nav.parts")),1),s("div",q,[s("div",M,[e[0]||(e[0]=s("span",{class:"ds-tag"},"DetailLayout",-1)),s("p",O,o(t(a)("design-system.section.detail-nav.part.layout")),1),e[1]||(e[1]=s("span",{class:"ds-spec"},"320px + minmax(0, 1fr)",-1))]),s("div",$,[e[2]||(e[2]=s("span",{class:"ds-tag"},"назад",-1)),s("p",F,o(t(a)("design-system.section.detail-nav.part.back")),1),e[3]||(e[3]=s("span",{class:"ds-spec"},"история → parent",-1))]),s("div",G,[e[4]||(e[4]=s("span",{class:"ds-tag"},"оформление",-1)),s("p",J,o(t(a)("design-system.section.detail-nav.part.appearance")),1),e[5]||(e[5]=s("span",{class:"ds-spec"},"карточка под панелью",-1))]),s("div",j,[e[6]||(e[6]=s("span",{class:"ds-tag"},"parent",-1)),s("p",z,o(t(a)("design-system.section.detail-nav.part.parent")),1),e[7]||(e[7]=s("span",{class:"ds-spec"},"один уровень вверх",-1))]),s("div",K,[e[8]||(e[8]=s("span",{class:"ds-tag"},"code",-1)),s("p",Q,o(t(a)("design-system.section.detail-nav.part.code")),1),e[9]||(e[9]=s("span",{class:"ds-spec"},"шапка + колонка",-1))]),s("div",U,[e[10]||(e[10]=s("span",{class:"ds-tag"},"DetailHead",-1)),s("p",W,o(t(a)("design-system.section.detail-nav.part.head")),1),e[11]||(e[11]=s("span",{class:"ds-spec"},"надпись над карточками",-1))]),s("div",X,[e[12]||(e[12]=s("span",{class:"ds-tag"},"обновить",-1)),s("p",Y,o(t(a)("design-system.section.detail-nav.part.refresh")),1),e[13]||(e[13]=s("span",{class:"ds-spec"},"правый край первой строки",-1))]),s("div",Z,[e[14]||(e[14]=s("span",{class:"ds-tag"},"more",-1)),s("p",ss,o(t(a)("design-system.section.detail-nav.part.more")),1),e[15]||(e[15]=s("span",{class:"ds-spec"},"слот, иначе кнопки нет",-1))])])]),s("section",es,[s("h6",ts,o(t(a)("design-system.section.detail-nav.markup")),1),n(i,{code:as,lang:"ts"}),n(i,{code:os,lang:"vue"})])])]),_:1}))}}),Vs=u(is,[["__scopeId","data-v-64427ecf"]]);export{Vs as default};
