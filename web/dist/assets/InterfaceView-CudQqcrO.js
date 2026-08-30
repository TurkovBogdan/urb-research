import{aQ as f,b9 as g,aJ as _,a2 as b,bB as c,aO as s,aN as h,bl as d,a7 as V,aL as O,aK as T,ad as v,bf as G,a6 as y,aD as S,bq as U,bv as F,c as M,O as D,Q as H,P as C,T as P,bn as e,aI as o,as as r,V as B,I as w,R as $,N as k,b as z,a as L,aE as Q,S as W}from"./index-DgoYO1jO.js";import{P as q}from"./PageHeader-C93-h_jI.js";import{M as J}from"./MarkdownRenderer-BJMLmIqZ.js";import{S as K}from"./SwitchPanel-C7s7dI28.js";import"./SectionHeader-C_w2_1Y4.js";import"./CodeBlock-CLVloEAm.js";import"./IconCode-C8qU1hKt.js";import"./IconCopy-DwcYywh9.js";import"./purify.es-DxCUJf2h.js";const Z={key:0,class:"settings-group__desc"},j=f({__name:"SettingsGroup",props:{title:{},description:{}},setup(p){return(t,i)=>(g(),_(b,{variant:"outlined",rounded:"lg"},{default:c(()=>[s(V,{class:"text-h6"},{default:c(()=>[h(d(p.title),1)]),_:1}),p.description?(g(),O("p",Z,d(p.description),1)):T("",!0),s(v),s(y,{class:"d-flex flex-column ga-6"},{default:c(()=>[G(t.$slots,"default",{},void 0,!0)]),_:3})]),_:3}))}}),u=S(j,[["__scopeId","data-v-81e729c1"]]),X={class:"settings-grid"},Y={class:"setting"},ee={class:"setting__desc"},te={class:"setting"},ie={class:"setting__desc"},se={class:"setting"},ae={class:"setting__desc"},le={class:"setting"},ne={class:"setting__desc"},oe={class:"setting"},de={class:"setting__desc"},re={class:"setting"},ce={class:"setting__desc"},pe={class:"setting"},me={class:"setting__desc"},ue={class:"setting"},ge={class:"setting__desc"},fe={class:"setting"},_e={class:"setting__desc"},be={class:"setting"},he={class:"setting__desc"},Ve=`# Заголовок первого уровня

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

Схема идёт в теле тем же блоком, что и код, и набрана своей гарнитурой — подписи внутри
блоков живут в тесных коробках, и семья, хорошая в абзаце, там может не поместиться.

\`\`\`mermaid
graph LR
  A[Запрос агента] --> B{Схема поддержана?}
  B -->|да| C[Рендер SVG]
  B -->|нет| D[Блок кода]
\`\`\`

---

Последний абзац после разделителя — самый широкий интервал в теле.
`,ve=f({__name:"InterfaceView",setup(p){const{t}=U(),i=F();function m(a){return{subtitle:a.note,style:{fontFamily:a.stack}}}function I(a){return{subtitle:a.note}}function E(a){return{subtitle:a.note}}const N=M.map(a=>({title:a===D?t("settings.interface.diagram.height.unlimited"):`${a} px`,value:a})),x=W.map(a=>({title:`${a} px`,value:a})),A=H.map(a=>({title:a===C?t("settings.interface.measure.reading.unlimited"):`${a}ch`,value:a})),R=P.map(a=>({title:t(a.label),value:a.code,props:{prependIcon:a.icon}}));return(a,l)=>(g(),_(Q,null,{default:c(()=>[s(q,{title:e(t)("settings.interface.page.title"),description:e(t)("settings.interface.page.description")},null,8,["title","description"]),o("div",X,[s(u,{title:e(t)("settings.interface.group.app.title"),description:e(t)("settings.interface.group.app.description")},{default:c(()=>[o("div",Y,[s(r,{modelValue:e(i).appearance.theme,"onUpdate:modelValue":l[0]||(l[0]=n=>e(i).appearance.theme=n),items:e(B),"item-title":"label","item-value":"code","item-props":I,chips:!1,label:e(t)("settings.interface.theme.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ee,d(e(t)("settings.interface.theme.description")),1)]),o("div",te,[s(r,{modelValue:e(i).typography.interfaceFont,"onUpdate:modelValue":l[1]||(l[1]=n=>e(i).typography.interfaceFont=n),items:e(w),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.interface.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ie,d(e(t)("settings.interface.font.interface.description")),1)]),o("div",se,[s(r,{modelValue:e(i).lists.researchView,"onUpdate:modelValue":l[2]||(l[2]=n=>e(i).lists.researchView=n),items:e(R),chips:!1,label:e(t)("settings.interface.list.research.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ae,d(e(t)("settings.interface.list.research.description")),1)]),s(K,{modelValue:e(i).ui.documentNav,"onUpdate:modelValue":l[3]||(l[3]=n=>e(i).ui.documentNav=n),title:e(t)("settings.interface.nav.document.label"),description:e(t)("settings.interface.nav.document.description")},null,8,["modelValue","title","description"])]),_:1},8,["title","description"]),s(u,{title:e(t)("settings.interface.group.document.title"),description:e(t)("settings.interface.group.document.description")},{default:c(()=>[o("div",le,[s(r,{modelValue:e(i).typography.readingFont,"onUpdate:modelValue":l[4]||(l[4]=n=>e(i).typography.readingFont=n),items:e($),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ne,d(e(t)("settings.interface.font.reading.description")),1)]),o("div",oe,[s(r,{modelValue:e(i).typography.readingSize,"onUpdate:modelValue":l[5]||(l[5]=n=>e(i).typography.readingSize=n),items:e(x),chips:!1,label:e(t)("settings.interface.size.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",de,d(e(t)("settings.interface.size.reading.description")),1)]),o("div",re,[s(r,{modelValue:e(i).typography.monoFont,"onUpdate:modelValue":l[6]||(l[6]=n=>e(i).typography.monoFont=n),items:e(k),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.mono.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ce,d(e(t)("settings.interface.font.mono.description")),1)]),o("div",pe,[s(r,{modelValue:e(i).typography.readingMeasure,"onUpdate:modelValue":l[7]||(l[7]=n=>e(i).typography.readingMeasure=n),items:e(A),chips:!1,label:e(t)("settings.interface.measure.reading.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",me,d(e(t)("settings.interface.measure.reading.description")),1)])]),_:1},8,["title","description"]),s(u,{title:e(t)("settings.interface.group.diagram.title"),description:e(t)("settings.interface.group.diagram.description")},{default:c(()=>[o("div",ue,[s(r,{modelValue:e(i).diagrams.font,"onUpdate:modelValue":l[8]||(l[8]=n=>e(i).diagrams.font=n),items:e(z),"item-title":"label","item-value":"code","item-props":m,chips:!1,label:e(t)("settings.interface.font.diagram.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",ge,d(e(t)("settings.interface.font.diagram.description")),1)]),o("div",fe,[s(r,{modelValue:e(i).diagrams.align,"onUpdate:modelValue":l[9]||(l[9]=n=>e(i).diagrams.align=n),items:e(L),"item-title":"label","item-value":"code","item-props":E,chips:!1,label:e(t)("settings.interface.diagram.align.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",_e,d(e(t)("settings.interface.diagram.align.description")),1)]),o("div",be,[s(r,{modelValue:e(i).diagrams.maxHeight,"onUpdate:modelValue":l[10]||(l[10]=n=>e(i).diagrams.maxHeight=n),items:e(N),chips:!1,label:e(t)("settings.interface.diagram.height.label"),variant:"outlined",density:"comfortable","hide-details":"auto"},null,8,["modelValue","items","label"]),o("p",he,d(e(t)("settings.interface.diagram.height.description")),1)])]),_:1},8,["title","description"])]),s(b,{variant:"outlined",rounded:"lg",class:"mt-4"},{default:c(()=>[s(V,{class:"text-h6"},{default:c(()=>[h(d(e(t)("settings.interface.preview.title")),1)]),_:1}),s(v),s(y,null,{default:c(()=>[s(J,{text:Ve})]),_:1})]),_:1})]),_:1}))}}),Te=S(ve,[["__scopeId","data-v-e5dde948"]]);export{Te as default};
