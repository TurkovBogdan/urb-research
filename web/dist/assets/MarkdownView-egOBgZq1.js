import{aI as f,be as g,aB as v,bo as i,aA as e,aG as t,bb as n,b9 as l,Q as p,aF as m,U as w,ar as _,aw as b,b0 as u,aZ as y,av as k}from"./index-Ck6Fpicj.js";import{P as x}from"./PageHeader-tc2LA7XG.js";import{M as c}from"./MarkdownRenderer-C97MjJiW.js";import"./CodeBlock-Mnz8eEBw.js";import"./IconCode-DQa8dIfp.js";import"./IconCopy-CnfBC-II.js";import"./purify.es-DxCUJf2h.js";const V={class:"ds-page"},B={class:"ds-section"},M={class:"mb-3"},R={class:"ds-card"},S={class:"ds-row"},P={class:"ds-controls"},T={class:"ds-section"},A={class:"mb-3"},C={class:"live-grid"},D={class:"live-pane"},I={class:"live-pane"},L={class:"preview-box"},F={class:"ds-section"},K={class:"mb-3"},N={class:"preview-box"},Q={class:"ds-section"},U={class:"mb-3"},E={class:"preview-box preview-box--narrow"},W=`# First-level heading

A regular paragraph with **bold text**, *italic* and \`inline code\`.

## Unordered list

- Develop and maintain backend services in Python
- Design REST APIs and integrate with external systems
- Review code, take part in architectural decisions
- Nested item:
  - Sub-item A
  - Sub-item B

## Ordered list

1. Write tests
2. Run CI
3. Ship to production

## Requirements

### Must have

- 3+ years of experience with Python 3.10+
- FastAPI / SQLAlchemy / PostgreSQL
- Understanding of asyncio and the event loop

### Nice to have

- Experience with queues (Celery, RabbitMQ, Redis)
- Knowledge of Docker and Kubernetes

## Code block

\`\`\`python
async def list_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    async with session_scope() as s:
        result = await s.execute(
            select(Vacancy).where(Vacancy.status == status).limit(limit)
        )
        return list(result.scalars())
\`\`\`

## Table

| Engine | Bundle (gzip) | Raw HTML by default | Notes |
|---|---:|:---:|---|
| markdown-it | 52.7 KB | off | plugin rules, GFM tables |
| marked | 12.5 KB | on | smallest, narrow extension model |
| unified | 36.8 KB | pipeline choice | full AST, largest ecosystem |

## Quote

> We are looking for a specialist ready to work in a fast-changing environment
> and not afraid of technical challenges.

## Task list

- [x] Migrate the renderer to markdown-it
- [ ] Wire syntax highlighting into body code blocks

---

Small text at the end of the paragraph with ~~a struck-out phrase~~, an [external link](https://example.com)
that opens in a new tab, and raw HTML like <b>this</b> which the parser escapes instead of rendering.`,h=`Requirements:
- 2+ years of experience as a Python Backend Developer
- Knowledge of Django or FastAPI
- Understanding of SOLID principles and clean code
- Experience with relational databases (PostgreSQL preferred)

What we offer:
- Remote work, 5/2 schedule
- Health insurance from the first month
- Corporate training and conferences at the company's expense
- Choice of equipment (Mac/Linux)

We offer interesting tasks, honest feedback and no bureaucracy.`,q=f({__name:"MarkdownView",setup(H){const o=u(!1),d=u(h),{t:a}=g();return(z,s)=>(y(),v(b,null,{default:i(()=>[e("div",V,[t(x,{title:n(a)("design-system.page.markdown.title"),description:n(a)("design-system.page.markdown.description"),"back-to":"/design-system"},null,8,["title","description"]),e("section",B,[e("h6",M,l(n(a)("design-system.section.markdown.props")),1),e("div",R,[e("div",S,[s[4]||(s[4]=e("span",{class:"ds-tag"},"compact",-1)),e("div",P,[t(w,{modelValue:o.value,"onUpdate:modelValue":s[0]||(s[0]=r=>o.value=r),mandatory:"",divided:"",density:"compact"},{default:i(()=>[t(p,{value:!1},{default:i(()=>[...s[2]||(s[2]=[m("false",-1)])]),_:1}),t(p,{value:!0},{default:i(()=>[...s[3]||(s[3]=[m("true",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[5]||(s[5]=e("span",{class:"ds-spec"},"reduces font-size and spacing",-1))])])]),e("section",T,[e("h6",A,l(n(a)("design-system.section.markdown.liveEditor")),1),e("div",C,[e("div",D,[s[6]||(s[6]=e("span",{class:"ds-tag mb-2"},"Markdown",-1)),t(_,{modelValue:d.value,"onUpdate:modelValue":s[1]||(s[1]=r=>d.value=r),variant:"outlined",density:"compact",rows:"14","hide-details":"",style:{"font-family":"var(--font-mono)","font-size":"12px"}},null,8,["modelValue"])]),e("div",I,[s[7]||(s[7]=e("span",{class:"ds-tag mb-2"},"Result",-1)),e("div",L,[t(c,{text:d.value,compact:o.value},null,8,["text","compact"])])])])]),e("section",F,[e("h6",K,l(n(a)("design-system.section.markdown.fullDemo")),1),e("div",N,[t(c,{text:W,compact:o.value},null,8,["compact"])])]),e("section",Q,[e("h6",U,l(n(a)("design-system.section.markdown.jobContent")),1),e("div",E,[t(c,{text:h,compact:o.value},null,8,["compact"])])])])]),_:1}))}}),Y=k(q,[["__scopeId","data-v-91947b39"]]);export{Y as default};
