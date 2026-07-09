import{ak as h,aN as v,ad as _,aX as i,ac as e,ai as t,aL as o,aK as d,t as p,ah as m,v as g,a6 as w,aD as u,aB as y,aa as x}from"./index-DucitkGq.js";import{_ as b}from"./PageLayout.vue_vue_type_script_setup_true_lang-BWR86Zx6.js";import{P as k}from"./PageHeader-BYf4O_Bt.js";import{M as c}from"./MarkdownRenderer-DTUXnJn9.js";import"./IconArrowLeft-D6XlGFor.js";import"./purify.es-DxCUJf2h.js";const V={class:"ds-page"},P={class:"ds-section"},D={class:"mb-3"},R={class:"ds-card"},S={class:"ds-row"},M={class:"ds-controls"},B={class:"ds-section"},C={class:"mb-3"},I={class:"live-grid"},L={class:"live-pane"},A={class:"live-pane"},N={class:"preview-box"},Q={class:"ds-section"},U={class:"mb-3"},q={class:"preview-box"},E={class:"ds-section"},F={class:"mb-3"},K={class:"preview-box preview-box--narrow"},T=`# First-level heading

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

## Quote

> We are looking for a specialist ready to work in a fast-changing environment
> and not afraid of technical challenges.

---

Small text at the end of the paragraph. Links are filtered by DOMPurify and shown as plain text.`,f=`Requirements:
- 2+ years of experience as a Python Backend Developer
- Knowledge of Django or FastAPI
- Understanding of SOLID principles and clean code
- Experience with relational databases (PostgreSQL preferred)

What we offer:
- Remote work, 5/2 schedule
- Health insurance from the first month
- Corporate training and conferences at the company's expense
- Choice of equipment (Mac/Linux)

We offer interesting tasks, honest feedback and no bureaucracy.`,W=h({__name:"MarkdownView",setup(O){const n=u(!1),l=u(f),{t:a}=v();return(j,s)=>(y(),_(b,null,{default:i(()=>[e("div",V,[t(k,{title:o(a)("design-system.page.markdown.title"),description:o(a)("design-system.page.markdown.description"),"back-to":"/design-system"},null,8,["title","description"]),e("section",P,[e("h6",D,d(o(a)("design-system.section.markdown.props")),1),e("div",R,[e("div",S,[s[4]||(s[4]=e("span",{class:"ds-tag"},"compact",-1)),e("div",M,[t(g,{modelValue:n.value,"onUpdate:modelValue":s[0]||(s[0]=r=>n.value=r),mandatory:"",divided:"",density:"compact"},{default:i(()=>[t(p,{value:!1},{default:i(()=>[...s[2]||(s[2]=[m("false",-1)])]),_:1}),t(p,{value:!0},{default:i(()=>[...s[3]||(s[3]=[m("true",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[5]||(s[5]=e("span",{class:"ds-spec"},"reduces font-size and spacing",-1))])])]),e("section",B,[e("h6",C,d(o(a)("design-system.section.markdown.liveEditor")),1),e("div",I,[e("div",L,[s[6]||(s[6]=e("span",{class:"ds-tag mb-2"},"Markdown",-1)),t(w,{modelValue:l.value,"onUpdate:modelValue":s[1]||(s[1]=r=>l.value=r),variant:"outlined",density:"compact",rows:"14","hide-details":"",style:{"font-family":"var(--font-mono)","font-size":"12px"}},null,8,["modelValue"])]),e("div",A,[s[7]||(s[7]=e("span",{class:"ds-tag mb-2"},"Result",-1)),e("div",N,[t(c,{text:l.value,compact:n.value},null,8,["text","compact"])])])])]),e("section",Q,[e("h6",U,d(o(a)("design-system.section.markdown.fullDemo")),1),e("div",q,[t(c,{text:T,compact:n.value},null,8,["compact"])])]),e("section",E,[e("h6",F,d(o(a)("design-system.section.markdown.jobContent")),1),e("div",K,[t(c,{text:f,compact:n.value},null,8,["compact"])])])])]),_:1}))}}),Y=x(W,[["__scopeId","data-v-3937f110"]]);export{Y as default};
