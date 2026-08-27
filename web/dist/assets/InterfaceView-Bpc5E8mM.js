import{aI as g,aZ as u,aB as _,W as b,bn as d,aG as s,aF as h,b9 as r,$ as V,aD as R,aC as C,a5 as v,b3 as T,_ as y,av as S,bd as A,bi as F,H as U,N as w,K as O,bb as e,aA as o,ak as c,T as k,I as M,R as P,aw as $,J as D}from"./index-CkfKdzXd.js";import{P as G}from"./PageHeader-jDU3yFLp.js";import{M as z}from"./MarkdownRenderer-C1IGRgz7.js";import{S as B}from"./SwitchPanel-C2bmPcKX.js";import"./CodeBlock-CJ5iYZdl.js";import"./IconCode-wyS4Fkd9.js";import"./IconCopy-CjHp9z5j.js";import"./purify.es-DxCUJf2h.js";const H={key:0,class:"settings-group__desc"},W=g({__name:"SettingsGroup",props:{title:{},description:{}},setup(p){return(t,a)=>(u(),_(b,{variant:"outlined",rounded:"lg"},{default:d(()=>[s(V,{class:"text-h6"},{default:d(()=>[h(r(p.title),1)]),_:1}),p.description?(u(),R("p",H,r(p.description),1)):C("",!0),s(v),s(y,{class:"d-flex flex-column ga-6"},{default:d(()=>[T(t.$slots,"default",{},void 0,!0)]),_:3})]),_:3}))}}),f=S(W,[["__scopeId","data-v-81e729c1"]]),Z={class:"settings-grid"},J={class:"setting"},K={class:"setting__desc"},L={class:"setting"},j={class:"setting__desc"},q={class:"setting"},Q={class:"setting__desc"},X={class:"setting"},Y={class:"setting__desc"},ee={class:"setting"},te={class:"setting__desc"},se={class:"setting"},ie={class:"setting__desc"},ae=`# Заголовок первого уровня

Первый абзац идёт сразу под заголовком — по нему видно рисунок строчных, интерлиньяж и,
главное, длину строки, на которой глаз ещё уверенно находит начало следующей. Длина строки
влияет на скорость чтения сильнее, чем кегль, поэтому колонка ограничена по ширине, а
таблицы и блоки кода из этого ограничения выведены — их просматривают, а не читают подряд.

## Заголовок второго уровня

Второй абзац — чтобы стало видно расстояние между разделами и то, что отступ над заголовком
заметно больше отступа под ним: заголовок принадлежит тексту, который идёт следом. Внутри
строки встречаются \`inline-код\`, **жирное выделение**, *курсив* и [внешняя ссылка](https://example.com),
а ещё пилюля ссылки на сущность — RESEARCH@ef8a7d2f258de68b188bda.

### Заголовок третьего уровня

- маркированный список: первый пункт
- второй пункт, заметно длиннее первого, чтобы стало видно, как ложится перенос внутри пункта
  - вложенный пункт
- третий пункт

1. нумерованный список
2. второй пункт

- [x] выполненный пункт чек-листа
- [ ] невыполненный пункт

> Цитата отбивается линейкой и воздухом, без курсива: в этих телах она бывает длиной
> в абзац, а курсив на такой длине читается заметно медленнее.

| Параметр | Значение | Комментарий |
|---|---|---|
| Кегль текста | 16 px | нижняя граница для чтения подряд |
| Интерлиньяж | 1.7 | абзацам нужно больше воздуха, чем строкам интерфейса |
| Длина строки | 92ch | таблицы и код в это ограничение не входят |

\`\`\`python
def read(text: str, *, size: int = 16) -> str:
    """Блок кода: подсветка, номера строк и копирование."""
    return text.strip()
\`\`\`

---

Последний абзац после разделителя — самый широкий интервал в теле.
`,ne=g({__name:"InterfaceView",setup(p){const{t}=A(),a=F();function m(i){return{subtitle:i.note,style:{fontFamily:i.stack}}}function E(i){return{subtitle:i.note}}const x=D.map(i=>({title:`${i} px`,value:i})),I=U.map(i=>({title:i===w?t("settings.interface.measure.reading.unlimited"):`${i}ch`,value:i})),N=O.map(i=>({title:t(i.label),value:i.code,props:{prependIcon:i.icon}}));return(i,n)=>(u(),_($,null,{default:d(()=>[s(G,{title:e(t)("settings.interface.page.title"),description:e(t)("settings.interface.page.description")},null,8,["title","description"]),o("div",Z,[s(f,{title:e(t)("settings.interface.group.app.title"),description:e(t)("settings.interface.group.app.description")},{default:d(()=>[o("div",J,[s(c,{modelValue:e(a).appearance.theme,"onUpdate:modelValue":n[0]||(n[0]=l=>e(a).appearance.theme=l),items:e(k),"item-title":"label","item-value":"code","item-props":E,chips:!1,label:e(t)("settings.interface.theme.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",K,r(e(t)("settings.interface.theme.description")),1)]),o("div",L,[s(c,{modelValue:e(a).typography.interfaceFont,"onUpdate:modelValue":n[1]||(n[1]=l=>e(a).typography.interfaceFont=l),items:e(M),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.interface.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",j,r(e(t)("settings.interface.font.interface.description")),1)]),o("div",q,[s(c,{modelValue:e(a).lists.researchView,"onUpdate:modelValue":n[2]||(n[2]=l=>e(a).lists.researchView=l),items:e(N),chips:!1,label:e(t)("settings.interface.list.research.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",Q,r(e(t)("settings.interface.list.research.description")),1)]),s(B,{modelValue:e(a).ui.documentNav,"onUpdate:modelValue":n[3]||(n[3]=l=>e(a).ui.documentNav=l),title:e(t)("settings.interface.nav.document.label"),description:e(t)("settings.interface.nav.document.description")},null,8,["modelValue","title","description"])]),_:1},8,["title","description"]),s(f,{title:e(t)("settings.interface.group.document.title"),description:e(t)("settings.interface.group.document.description")},{default:d(()=>[o("div",X,[s(c,{modelValue:e(a).typography.readingFont,"onUpdate:modelValue":n[4]||(n[4]=l=>e(a).typography.readingFont=l),items:e(P),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",Y,r(e(t)("settings.interface.font.reading.description")),1)]),o("div",ee,[s(c,{modelValue:e(a).typography.readingSize,"onUpdate:modelValue":n[5]||(n[5]=l=>e(a).typography.readingSize=l),items:e(x),chips:!1,label:e(t)("settings.interface.size.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",te,r(e(t)("settings.interface.size.reading.description")),1)]),o("div",se,[s(c,{modelValue:e(a).typography.readingMeasure,"onUpdate:modelValue":n[6]||(n[6]=l=>e(a).typography.readingMeasure=l),items:e(I),chips:!1,label:e(t)("settings.interface.measure.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ie,r(e(t)("settings.interface.measure.reading.description")),1)])]),_:1},8,["title","description"])]),s(b,{variant:"outlined",rounded:"lg",class:"mt-4"},{default:d(()=>[s(V,{class:"text-h6"},{default:d(()=>[h(r(e(t)("settings.interface.preview.title")),1)]),_:1}),s(v),s(y,null,{default:d(()=>[s(z,{text:ae})]),_:1})]),_:1})]),_:1}))}}),fe=S(ne,[["__scopeId","data-v-7a19fad5"]]);export{fe as default};
