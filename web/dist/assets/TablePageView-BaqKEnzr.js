import{aI as f,be as _,aB as y,bo as m,aA as e,aG as i,bb as a,b9 as o,aq as h,a5 as C,a3 as V,W as w,aw as S,b0 as g,az as T,aZ as k,av as x}from"./index-Ck6Fpicj.js";import{I as z}from"./IconSearch-YkHcmrbI.js";import{P}from"./PageHeader-tc2LA7XG.js";import{T as B}from"./TablePaginationBar-jaUXdJyy.js";import{C as b}from"./CodeBlock-Mnz8eEBw.js";import"./IconCode-DQa8dIfp.js";import"./IconCopy-CnfBC-II.js";const R={class:"ds-page"},E={class:"ds-section"},A={class:"mb-3"},D={class:"ds-note"},H={class:"filter-panel"},I={class:"ds-section"},U={class:"mb-3"},L={class:"ds-card"},M={class:"ds-row"},q={class:"ds-part"},N={class:"ds-row"},W={class:"ds-part"},F={class:"ds-row"},G={class:"ds-part"},O={class:"ds-row"},Z={class:"ds-part"},$={class:"ds-section"},j={class:"mb-3"},J={class:"ds-note"},K=`<!-- Панель фильтров ВНУТРИ карточки таблицы: строки своих рамок не имеют,
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
</VCard>`,X=f({__name:"TablePageView",setup(Y){const{t}=_(),u=[{code:"RESEARCH@8c1f…",title:"Ubuntu 26.04 LTS: первичная настройка",areas:6,sources:27,updated:"27.08.2026 23:48"},{code:"RESEARCH@2a0d…",title:"Типографика и система отступов",areas:8,sources:11,updated:"27.08.2026 08:22"},{code:"RESEARCH@8913…",title:"Движок рендера Markdown для фронта",areas:7,sources:9,updated:"27.08.2026 08:22"},{code:"RESEARCH@c176…",title:"Глобальные экраны ошибок портала",areas:4,sources:0,updated:"27.08.2026 08:21"}],v=[{title:t("design-system.section.table-page.column.title"),key:"title"},{title:t("design-system.section.table-page.column.areas"),key:"areas",width:90,align:"end"},{title:t("design-system.section.table-page.column.sources"),key:"sources",width:110,align:"end"},{title:t("design-system.section.table-page.column.updated"),key:"updated",width:190}],l=g(""),r=g(1),d=g(25),p=T(()=>{const c=l.value.trim().toLowerCase();return c?u.filter(s=>s.title.toLowerCase().includes(c)):u});return(c,s)=>(k(),y(S,null,{default:m(()=>[e("div",R,[i(P,{title:a(t)("design-system.page.table-page.title"),description:a(t)("design-system.page.table-page.description"),"back-to":"/design-system"},null,8,["title","description"]),e("section",E,[e("h6",A,o(a(t)("design-system.section.table-page.assembled")),1),e("p",D,o(a(t)("design-system.section.table-page.assembled_note")),1),i(w,{variant:"outlined",rounded:"lg"},{default:m(()=>[e("div",H,[i(h,{modelValue:l.value,"onUpdate:modelValue":s[0]||(s[0]=n=>l.value=n),label:a(t)("design-system.section.table-page.filter"),"prepend-inner-icon":a(z),variant:"outlined",density:"comfortable","hide-details":"",clearable:""},null,8,["modelValue","label","prepend-inner-icon"])]),i(C),i(V,{headers:v,items:p.value,"items-per-page":d.value,"item-value":"code",density:"comfortable",hover:"","hide-default-footer":"","no-data-text":a(t)("design-system.section.table-page.empty")},null,8,["items","items-per-page","no-data-text"]),i(B,{page:r.value,"page-size":d.value,total:p.value.length,"page-count":Math.max(1,Math.ceil(p.value.length/d.value)),"onUpdate:page":s[1]||(s[1]=n=>r.value=n),"onUpdate:pageSize":s[2]||(s[2]=n=>{d.value=n,r.value=1})},null,8,["page","page-size","total","page-count"])]),_:1})]),e("section",I,[e("h6",U,o(a(t)("design-system.section.table-page.parts")),1),e("div",L,[e("div",M,[s[3]||(s[3]=e("span",{class:"ds-tag"},"filters",-1)),e("p",q,o(a(t)("design-system.section.table-page.part.filters")),1),s[4]||(s[4]=e("span",{class:"ds-spec"},"VCard > .filter-panel",-1))]),e("div",N,[s[5]||(s[5]=e("span",{class:"ds-tag"},"head",-1)),e("p",W,o(a(t)("design-system.section.table-page.part.head")),1),s[6]||(s[6]=e("span",{class:"ds-spec"},"11px / uppercase",-1))]),e("div",F,[s[7]||(s[7]=e("span",{class:"ds-tag"},"rows",-1)),e("p",G,o(a(t)("design-system.section.table-page.part.rows")),1),s[8]||(s[8]=e("span",{class:"ds-spec"},"hover, @click:row",-1))]),e("div",O,[s[9]||(s[9]=e("span",{class:"ds-tag"},"footer",-1)),e("p",Z,o(a(t)("design-system.section.table-page.part.footer")),1),s[10]||(s[10]=e("span",{class:"ds-spec"},"TablePaginationBar",-1))])])]),e("section",$,[e("h6",j,o(a(t)("design-system.section.table-page.placement")),1),e("p",J,o(a(t)("design-system.section.table-page.placement_note")),1),i(b,{code:K,lang:"vue"}),s[11]||(s[11]=e("div",{class:"ds-gap"},null,-1)),i(b,{code:Q,lang:"vue"})])])]),_:1}))}}),de=x(X,[["__scopeId","data-v-34333ed8"]]);export{de as default};
