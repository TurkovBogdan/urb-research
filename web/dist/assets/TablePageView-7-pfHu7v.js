import{aT as f,by as _,aM as y,bJ as m,aL as e,aR as i,bt as a,br as o,aB as h,ag as C,ae as V,a5 as w,aH as S,bi as g,aK as T,be as k,aG as x}from"./index-BtmwolUh.js";import{I as P}from"./IconSearch-CzvU430s.js";import{P as R}from"./PageHeader-6n3hWajG.js";import{T as z}from"./TablePaginationBar-Bnu-C6SN.js";import{C as b}from"./CodeBlock-C9WSmWLc.js";import"./SectionHeader-CLcXhc8W.js";import"./IconCode-BhAPfniH.js";import"./IconCopy-BMYTMgpo.js";const B={class:"ds-page"},E={class:"ds-section"},H={class:"mb-3"},D={class:"ds-note"},A={class:"filter-panel"},I={class:"ds-section"},L={class:"mb-3"},M={class:"ds-card"},U={class:"ds-row"},N={class:"ds-part"},q={class:"ds-row"},F={class:"ds-part"},G={class:"ds-row"},J={class:"ds-part"},K={class:"ds-row"},O={class:"ds-part"},W={class:"ds-section"},$={class:"mb-3"},j={class:"ds-note"},Q=`<!-- Панель фильтров ВНУТРИ карточки таблицы: строки своих рамок не имеют,
     поэтому панель и строки живут в одной карточке, отбитые линейкой. -->
<VCard variant="outlined" rounded="lg">
  <div class="filter-panel">…поля фильтров…</div>
  <VDivider />

  <VDataTable
    :headers="headers"
    :items="store.items"
    :loading="store.loading"
    :items-per-page="store.pageSize"
    item-value="code"
    density="comfortable"
    hover
    hide-default-footer
    :no-data-text="emptyText"
    @click:row="open"
  />

  <TablePaginationBar
    :page="store.page"
    :page-size="store.pageSize"
    :total="store.total"
    :page-count="store.pageCount"
    @update:page="onPageChange"
    @update:page-size="onPageSizeChange"
  />
</VCard>`,X=`<!-- Плитки: карточка сама себе рамка, и общая карточка вокруг дала бы рамку в рамке.
     Поэтому у панели и у постраничности СВОИ карточки, а сетка лежит на полотне. -->
<VCard variant="outlined" rounded="lg" class="filter-panel mb-3">…поля фильтров…</VCard>

<div class="cards__grid">…плитки…</div>

<VCard variant="outlined" rounded="lg" class="mt-3">
  <TablePaginationBar … :divider="false" />
</VCard>`,Y=f({__name:"TablePageView",setup(Z){const{t}=_(),u=[{code:"RESEARCH@8c1f…",title:"Ubuntu 26.04 LTS: первичная настройка",areas:6,sources:27,updated:"27.08.2026 23:48"},{code:"RESEARCH@2a0d…",title:"Типографика и система отступов",areas:8,sources:11,updated:"27.08.2026 08:22"},{code:"RESEARCH@8913…",title:"Движок рендера Markdown для фронта",areas:7,sources:9,updated:"27.08.2026 08:22"},{code:"RESEARCH@c176…",title:"Глобальные экраны ошибок портала",areas:4,sources:0,updated:"27.08.2026 08:21"}],v=[{title:t("design-system.section.table-page.column.title"),key:"title"},{title:t("design-system.section.table-page.column.areas"),key:"areas",width:90,align:"end"},{title:t("design-system.section.table-page.column.sources"),key:"sources",width:110,align:"end"},{title:t("design-system.section.table-page.column.updated"),key:"updated",width:190}],l=g(""),r=g(1),d=g(25),p=T(()=>{const c=l.value.trim().toLowerCase();return c?u.filter(s=>s.title.toLowerCase().includes(c)):u});return(c,s)=>(k(),y(S,null,{default:m(()=>[e("div",B,[i(R,{title:a(t)("design-system.page.table-page.title"),description:a(t)("design-system.page.table-page.description"),"back-to":"/design-system"},null,8,["title","description"]),e("section",E,[e("h6",H,o(a(t)("design-system.section.table-page.assembled")),1),e("p",D,o(a(t)("design-system.section.table-page.assembled_note")),1),i(w,{variant:"outlined",rounded:"lg"},{default:m(()=>[e("div",A,[i(h,{modelValue:l.value,"onUpdate:modelValue":s[0]||(s[0]=n=>l.value=n),label:a(t)("design-system.section.table-page.filter"),"prepend-inner-icon":a(P),variant:"outlined",density:"comfortable","hide-details":"",clearable:""},null,8,["modelValue","label","prepend-inner-icon"])]),i(C),i(V,{headers:v,items:p.value,"items-per-page":d.value,"item-value":"code",density:"comfortable",hover:"","hide-default-footer":"","no-data-text":a(t)("design-system.section.table-page.empty")},null,8,["items","items-per-page","no-data-text"]),i(z,{page:r.value,"page-size":d.value,total:p.value.length,"page-count":Math.max(1,Math.ceil(p.value.length/d.value)),"onUpdate:page":s[1]||(s[1]=n=>r.value=n),"onUpdate:pageSize":s[2]||(s[2]=n=>{d.value=n,r.value=1})},null,8,["page","page-size","total","page-count"])]),_:1})]),e("section",I,[e("h6",L,o(a(t)("design-system.section.table-page.parts")),1),e("div",M,[e("div",U,[s[3]||(s[3]=e("span",{class:"ds-tag"},"filters",-1)),e("p",N,o(a(t)("design-system.section.table-page.part.filters")),1),s[4]||(s[4]=e("span",{class:"ds-spec"},"VCard > .filter-panel",-1))]),e("div",q,[s[5]||(s[5]=e("span",{class:"ds-tag"},"head",-1)),e("p",F,o(a(t)("design-system.section.table-page.part.head")),1),s[6]||(s[6]=e("span",{class:"ds-spec"},"11px / uppercase",-1))]),e("div",G,[s[7]||(s[7]=e("span",{class:"ds-tag"},"rows",-1)),e("p",J,o(a(t)("design-system.section.table-page.part.rows")),1),s[8]||(s[8]=e("span",{class:"ds-spec"},"hover, @click:row",-1))]),e("div",K,[s[9]||(s[9]=e("span",{class:"ds-tag"},"footer",-1)),e("p",O,o(a(t)("design-system.section.table-page.part.footer")),1),s[10]||(s[10]=e("span",{class:"ds-spec"},"TablePaginationBar",-1))])])]),e("section",W,[e("h6",$,o(a(t)("design-system.section.table-page.placement")),1),e("p",j,o(a(t)("design-system.section.table-page.placement_note")),1),i(b,{code:Q,lang:"vue"}),s[11]||(s[11]=e("div",{class:"ds-gap"},null,-1)),i(b,{code:X,lang:"vue"})])])]),_:1}))}}),le=x(Y,[["__scopeId","data-v-34333ed8"]]);export{le as default};
