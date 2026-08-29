import{aQ as r,bq as l,aJ as c,bB as d,aI as s,aO as n,bn as t,bl as o,ah as p,aj as m,aN as _,aE as v,b9 as h,aD as g}from"./index-DgiVIKDN.js";import{I as u}from"./IconFolderPlus-DaZK8IYv.js";import{P as y}from"./PageHeader-QCiJcUA-.js";import{D as f}from"./DetailNav-B8Ph60oH.js";import{D as b}from"./DetailHead-B7Xhiiv0.js";import{C as i}from"./CodeBlock-ByV1_rgQ.js";import"./SectionHeader-DbPwDl_7.js";import"./IconSettings-Drq9eSF2.js";import"./IconCopy-DfxKZXSa.js";import"./useClipboard-CLastNv4.js";import"./IconCode-LjzBA-r4.js";const D={class:"ds-page"},w={class:"ds-section"},E={class:"mb-3"},V={class:"ds-note"},C={class:"ds-section"},N={class:"mb-3"},P={class:"ds-note"},S={class:"ds-frame ds-rail"},k={class:"ds-section"},x={class:"mb-3"},H={class:"ds-note"},I={class:"ds-frame"},A={class:"ds-shelf"},L={class:"ds-title"},R={class:"ds-section"},T={class:"mb-3"},B={class:"ds-card"},q={class:"ds-row"},M={class:"ds-part"},O={class:"ds-row"},$={class:"ds-part"},j={class:"ds-row"},F={class:"ds-part"},G={class:"ds-row"},J={class:"ds-part"},Q={class:"ds-row"},z={class:"ds-part"},K={class:"ds-row"},U={class:"ds-part"},W={class:"ds-row"},X={class:"ds-part"},Y={class:"ds-row"},Z={class:"ds-part"},ss={class:"ds-section"},es={class:"mb-3"},ts="RESEARCH@bc854947af58733bd93c3d",as=`// routes.ts — деталки дети общей рамки
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
</template>`,ns="const parentPath = computed(() =>\n  source.value ? `/research/areas/${source.value.area_code}` : '/research/researches',\n)",ds="/design-system/detail-nav",is=r({__name:"DetailNavView",setup(rs){const{t:a}=l();return(ls,e)=>(h(),c(v,null,{default:d(()=>[s("div",D,[n(y,{title:t(a)("design-system.page.detail-nav.title"),description:t(a)("design-system.page.detail-nav.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",w,[s("h6",E,o(t(a)("design-system.section.detail-nav.rule")),1),s("p",V,o(t(a)("design-system.section.detail-nav.rule_note")),1)]),s("section",C,[s("h6",N,o(t(a)("design-system.section.detail-nav.panel")),1),s("p",P,o(t(a)("design-system.section.detail-nav.panel_note")),1),s("div",S,[n(f,{parent:ds,label:t(a)("design-system.section.detail-nav.sample.exit"),appearance:""},null,8,["label"])]),n(i,{code:ns,lang:"ts"})]),s("section",k,[s("h6",x,o(t(a)("design-system.section.detail-nav.head")),1),s("p",H,o(t(a)("design-system.section.detail-nav.head_note")),1),s("div",I,[n(b,{code:ts},{more:d(()=>[n(p,{"prepend-icon":t(u)},{default:d(()=>[n(m,null,{default:d(()=>[_(o(t(a)("design-system.section.detail-nav.sample.move_group")),1)]),_:1})]),_:1},8,["prepend-icon"])]),above:d(()=>[s("span",A,o(t(a)("design-system.section.detail-nav.sample.shelf")),1)]),default:d(()=>[s("h1",L,o(t(a)("design-system.section.detail-nav.sample.title")),1)]),_:1})])]),s("section",R,[s("h6",T,o(t(a)("design-system.section.detail-nav.parts")),1),s("div",B,[s("div",q,[e[0]||(e[0]=s("span",{class:"ds-tag"},"DetailLayout",-1)),s("p",M,o(t(a)("design-system.section.detail-nav.part.layout")),1),e[1]||(e[1]=s("span",{class:"ds-spec"},"320px + minmax(0, 1fr)",-1))]),s("div",O,[e[2]||(e[2]=s("span",{class:"ds-tag"},"назад",-1)),s("p",$,o(t(a)("design-system.section.detail-nav.part.back")),1),e[3]||(e[3]=s("span",{class:"ds-spec"},"история → parent",-1))]),s("div",j,[e[4]||(e[4]=s("span",{class:"ds-tag"},"оформление",-1)),s("p",F,o(t(a)("design-system.section.detail-nav.part.appearance")),1),e[5]||(e[5]=s("span",{class:"ds-spec"},"карточка под панелью",-1))]),s("div",G,[e[6]||(e[6]=s("span",{class:"ds-tag"},"parent",-1)),s("p",J,o(t(a)("design-system.section.detail-nav.part.parent")),1),e[7]||(e[7]=s("span",{class:"ds-spec"},"один уровень вверх",-1))]),s("div",Q,[e[8]||(e[8]=s("span",{class:"ds-tag"},"code",-1)),s("p",z,o(t(a)("design-system.section.detail-nav.part.code")),1),e[9]||(e[9]=s("span",{class:"ds-spec"},"вторая и последняя кнопка",-1))]),s("div",K,[e[10]||(e[10]=s("span",{class:"ds-tag"},"DetailHead",-1)),s("p",U,o(t(a)("design-system.section.detail-nav.part.head")),1),e[11]||(e[11]=s("span",{class:"ds-spec"},"надпись над карточками",-1))]),s("div",W,[e[12]||(e[12]=s("span",{class:"ds-tag"},"обновить",-1)),s("p",X,o(t(a)("design-system.section.detail-nav.part.refresh")),1),e[13]||(e[13]=s("span",{class:"ds-spec"},"правый край первой строки",-1))]),s("div",Y,[e[14]||(e[14]=s("span",{class:"ds-tag"},"more",-1)),s("p",Z,o(t(a)("design-system.section.detail-nav.part.more")),1),e[15]||(e[15]=s("span",{class:"ds-spec"},"слот, иначе кнопки нет",-1))])])]),s("section",ss,[s("h6",es,o(t(a)("design-system.section.detail-nav.markup")),1),n(i,{code:as,lang:"ts"}),n(i,{code:os,lang:"vue"})])])]),_:1}))}}),Ds=g(is,[["__scopeId","data-v-02ad55ac"]]);export{Ds as default};
