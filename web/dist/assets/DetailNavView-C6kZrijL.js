import{aT as l,by as c,aM as p,bJ as d,aL as s,aR as n,bt as t,br as o,ak as m,am as _,aQ as v,aH as h,be as g,aG as u}from"./index-BtmwolUh.js";import{I as y}from"./IconFolderPlus-BRHRUDzn.js";import{P as f}from"./PageHeader-6n3hWajG.js";import{D as b}from"./DetailNav-DI3vK18k.js";import{D}from"./DetailHead-UTK_7roD.js";import{C as i}from"./CodeBlock-C9WSmWLc.js";import"./SectionHeader-CLcXhc8W.js";import"./IconCopy-BMYTMgpo.js";import"./IconSettings-D6fYpV7r.js";import"./useClipboard-DwS-Jpac.js";import"./IconDotsVertical-BbhDGVEc.js";import"./CopyCodeButton-DdfdmwT8.js";import"./IconCode-BhAPfniH.js";const w={class:"ds-page"},V={class:"ds-section"},k={class:"mb-3"},C={class:"ds-note"},E={class:"ds-section"},P={class:"mb-3"},S={class:"ds-note"},x={class:"ds-frame ds-rail"},H={class:"ds-section"},N={class:"mb-3"},L={class:"ds-note"},R={class:"ds-frame"},T={class:"ds-shelf"},A={class:"ds-title"},I={class:"ds-section"},B={class:"mb-3"},M={class:"ds-card"},q={class:"ds-row"},G={class:"ds-part"},$={class:"ds-row"},F={class:"ds-part"},J={class:"ds-row"},O={class:"ds-part"},Q={class:"ds-row"},j={class:"ds-part"},z={class:"ds-row"},K={class:"ds-part"},U={class:"ds-row"},W={class:"ds-part"},X={class:"ds-row"},Y={class:"ds-part"},Z={class:"ds-row"},ss={class:"ds-part"},es={class:"ds-section"},ts={class:"mb-3"},r="RESEARCH@bc854947af58733bd93c3d",as=`// routes.ts — деталки дети общей рамки
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
</template>`,ns="const parentPath = computed(() =>\n  source.value ? `/research/areas/${source.value.area_code}` : '/research/researches',\n)",ds="/design-system/detail-nav",is=l({__name:"DetailNavView",setup(rs){const{t:a}=c();return(ls,e)=>(g(),p(h,null,{default:d(()=>[s("div",w,[n(f,{title:t(a)("design-system.page.detail-nav.title"),description:t(a)("design-system.page.detail-nav.description"),"back-to":"/design-system"},null,8,["title","description"]),s("section",V,[s("h6",k,o(t(a)("design-system.section.detail-nav.rule")),1),s("p",C,o(t(a)("design-system.section.detail-nav.rule_note")),1)]),s("section",E,[s("h6",P,o(t(a)("design-system.section.detail-nav.panel")),1),s("p",S,o(t(a)("design-system.section.detail-nav.panel_note")),1),s("div",x,[n(b,{parent:ds,label:t(a)("design-system.section.detail-nav.sample.exit"),code:r,appearance:""},null,8,["label"])]),n(i,{code:ns,lang:"ts"})]),s("section",H,[s("h6",N,o(t(a)("design-system.section.detail-nav.head")),1),s("p",L,o(t(a)("design-system.section.detail-nav.head_note")),1),s("div",R,[n(D,{code:r},{more:d(()=>[n(m,{"prepend-icon":t(y)},{default:d(()=>[n(_,null,{default:d(()=>[v(o(t(a)("design-system.section.detail-nav.sample.move_group")),1)]),_:1})]),_:1},8,["prepend-icon"])]),above:d(()=>[s("span",T,o(t(a)("design-system.section.detail-nav.sample.shelf")),1)]),default:d(()=>[s("h1",A,o(t(a)("design-system.section.detail-nav.sample.title")),1)]),_:1})])]),s("section",I,[s("h6",B,o(t(a)("design-system.section.detail-nav.parts")),1),s("div",M,[s("div",q,[e[0]||(e[0]=s("span",{class:"ds-tag"},"DetailLayout",-1)),s("p",G,o(t(a)("design-system.section.detail-nav.part.layout")),1),e[1]||(e[1]=s("span",{class:"ds-spec"},"320px + minmax(0, 1fr)",-1))]),s("div",$,[e[2]||(e[2]=s("span",{class:"ds-tag"},"назад",-1)),s("p",F,o(t(a)("design-system.section.detail-nav.part.back")),1),e[3]||(e[3]=s("span",{class:"ds-spec"},"история → parent",-1))]),s("div",J,[e[4]||(e[4]=s("span",{class:"ds-tag"},"оформление",-1)),s("p",O,o(t(a)("design-system.section.detail-nav.part.appearance")),1),e[5]||(e[5]=s("span",{class:"ds-spec"},"карточка под панелью",-1))]),s("div",Q,[e[6]||(e[6]=s("span",{class:"ds-tag"},"parent",-1)),s("p",j,o(t(a)("design-system.section.detail-nav.part.parent")),1),e[7]||(e[7]=s("span",{class:"ds-spec"},"один уровень вверх",-1))]),s("div",z,[e[8]||(e[8]=s("span",{class:"ds-tag"},"code",-1)),s("p",K,o(t(a)("design-system.section.detail-nav.part.code")),1),e[9]||(e[9]=s("span",{class:"ds-spec"},"шапка + колонка",-1))]),s("div",U,[e[10]||(e[10]=s("span",{class:"ds-tag"},"DetailHead",-1)),s("p",W,o(t(a)("design-system.section.detail-nav.part.head")),1),e[11]||(e[11]=s("span",{class:"ds-spec"},"надпись над карточками",-1))]),s("div",X,[e[12]||(e[12]=s("span",{class:"ds-tag"},"обновить",-1)),s("p",Y,o(t(a)("design-system.section.detail-nav.part.refresh")),1),e[13]||(e[13]=s("span",{class:"ds-spec"},"правый край первой строки",-1))]),s("div",Z,[e[14]||(e[14]=s("span",{class:"ds-tag"},"more",-1)),s("p",ss,o(t(a)("design-system.section.detail-nav.part.more")),1),e[15]||(e[15]=s("span",{class:"ds-spec"},"слот, иначе кнопки нет",-1))])])]),s("section",es,[s("h6",ts,o(t(a)("design-system.section.detail-nav.markup")),1),n(i,{code:as,lang:"ts"}),n(i,{code:os,lang:"vue"})])])]),_:1}))}}),Vs=u(is,[["__scopeId","data-v-64427ecf"]]);export{Vs as default};
