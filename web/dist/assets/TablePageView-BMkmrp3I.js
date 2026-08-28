import{aJ as f,bf as _,aC as y,bp as m,aB as e,aH as i,bc as a,ba as o,ar as C,a6 as h,a4 as V,X as w,ax as S,b1 as g,aA as x,a_ as T,aw as k}from"./index-Ds9idVhQ.js";import{I as P}from"./IconSearch-BwnWx9be.js";import{P as z}from"./PageHeader-lb5nyZ8w.js";import{T as B}from"./TablePaginationBar-CywlCevT.js";import{C as b}from"./CodeBlock-DfR0HDMM.js";import"./IconCode-CemdCWvb.js";import"./IconCopy-CRV5tP8E.js";const R={class:"ds-page"},E={class:"ds-section"},H={class:"mb-3"},A={class:"ds-note"},D={class:"filter-panel"},I={class:"ds-section"},U={class:"mb-3"},L={class:"ds-card"},M={class:"ds-row"},N={class:"ds-part"},q={class:"ds-row"},F={class:"ds-part"},J={class:"ds-row"},O={class:"ds-part"},W={class:"ds-row"},X={class:"ds-part"},$={class:"ds-section"},j={class:"mb-3"},G={class:"ds-note"},K=`<!-- Панель фильтров ВНУТРИ карточки таблицы: строки своих рамок не имеют,
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
</VCard>`,Q=`<!-- Плитки: карточка сама себе рамка, и общая карточка вокруг дала бы рамку в рамке.
     Поэтому у панели и у постраничности СВОИ карточки, а сетка лежит на полотне. -->
<VCard variant="outlined" rounded="lg" class="filter-panel mb-3">…поля фильтров…</VCard>

<div class="cards__grid">…плитки…</div>

<VCard variant="outlined" rounded="lg" class="mt-3">
  <TablePaginationBar … :divider="false" />
</VCard>`,Y=f({__name:"TablePageView",setup(Z){const{t}=_(),u=[{code:"RESEARCH@8c1f…",title:"Ubuntu 26.04 LTS: первичная настройка",areas:6,sources:27,updated:"27.08.2026 23:48"},{code:"RESEARCH@2a0d…",title:"Типографика и система отступов",areas:8,sources:11,updated:"27.08.2026 08:22"},{code:"RESEARCH@8913…",title:"Движок рендера Markdown для фронта",areas:7,sources:9,updated:"27.08.2026 08:22"},{code:"RESEARCH@c176…",title:"Глобальные экраны ошибок портала",areas:4,sources:0,updated:"27.08.2026 08:21"}],v=[{title:t("design-system.section.table-page.column.title"),key:"title"},{title:t("design-system.section.table-page.column.areas"),key:"areas",width:90,align:"end"},{title:t("design-system.section.table-page.column.sources"),key:"sources",width:110,align:"end"},{title:t("design-system.section.table-page.column.updated"),key:"updated",width:190}],l=g(""),r=g(1),d=g(25),p=x(()=>{const c=l.value.trim().toLowerCase();return c?u.filter(s=>s.title.toLowerCase().includes(c)):u});return(c,s)=>(T(),y(S,null,{default:m(()=>[e("div",R,[i(z,{title:a(t)("design-system.page.table-page.title"),description:a(t)("design-system.page.table-page.description"),"back-to":"/design-system"},null,8,["title","description"]),e("section",E,[e("h6",H,o(a(t)("design-system.section.table-page.assembled")),1),e("p",A,o(a(t)("design-system.section.table-page.assembled_note")),1),i(w,{variant:"outlined",rounded:"lg"},{default:m(()=>[e("div",D,[i(C,{modelValue:l.value,"onUpdate:modelValue":s[0]||(s[0]=n=>l.value=n),label:a(t)("design-system.section.table-page.filter"),"prepend-inner-icon":a(P),variant:"outlined",density:"comfortable","hide-details":"",clearable:""},null,8,["modelValue","label","prepend-inner-icon"])]),i(h),i(V,{headers:v,items:p.value,"items-per-page":d.value,"item-value":"code",density:"comfortable",hover:"","hide-default-footer":"","no-data-text":a(t)("design-system.section.table-page.empty")},null,8,["items","items-per-page","no-data-text"]),i(B,{page:r.value,"page-size":d.value,total:p.value.length,"page-count":Math.max(1,Math.ceil(p.value.length/d.value)),"onUpdate:page":s[1]||(s[1]=n=>r.value=n),"onUpdate:pageSize":s[2]||(s[2]=n=>{d.value=n,r.value=1})},null,8,["page","page-size","total","page-count"])]),_:1})]),e("section",I,[e("h6",U,o(a(t)("design-system.section.table-page.parts")),1),e("div",L,[e("div",M,[s[3]||(s[3]=e("span",{class:"ds-tag"},"filters",-1)),e("p",N,o(a(t)("design-system.section.table-page.part.filters")),1),s[4]||(s[4]=e("span",{class:"ds-spec"},"VCard > .filter-panel",-1))]),e("div",q,[s[5]||(s[5]=e("span",{class:"ds-tag"},"head",-1)),e("p",F,o(a(t)("design-system.section.table-page.part.head")),1),s[6]||(s[6]=e("span",{class:"ds-spec"},"11px / uppercase",-1))]),e("div",J,[s[7]||(s[7]=e("span",{class:"ds-tag"},"rows",-1)),e("p",O,o(a(t)("design-system.section.table-page.part.rows")),1),s[8]||(s[8]=e("span",{class:"ds-spec"},"hover, @click:row",-1))]),e("div",W,[s[9]||(s[9]=e("span",{class:"ds-tag"},"footer",-1)),e("p",X,o(a(t)("design-system.section.table-page.part.footer")),1),s[10]||(s[10]=e("span",{class:"ds-spec"},"TablePaginationBar",-1))])])]),e("section",$,[e("h6",j,o(a(t)("design-system.section.table-page.placement")),1),e("p",G,o(a(t)("design-system.section.table-page.placement_note")),1),i(b,{code:K,lang:"vue"}),s[11]||(s[11]=e("div",{class:"ds-gap"},null,-1)),i(b,{code:Q,lang:"vue"})])])]),_:1}))}}),de=k(Y,[["__scopeId","data-v-34333ed8"]]);export{de as default};
