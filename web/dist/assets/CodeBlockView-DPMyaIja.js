import{aJ as V,bf as h,aC as k,bp as t,aB as a,aH as e,bc as o,ba as r,W as f,S as i,aG as d,X as u,aE as w,b3 as B,F as C,ax as x,b1 as y,a_ as g,aw as E}from"./index-Ds9idVhQ.js";import{P as I}from"./PageHeader-lb5nyZ8w.js";import{C as l}from"./CodeBlock-DfR0HDMM.js";import"./IconCode-CemdCWvb.js";import"./IconCopy-CRV5tP8E.js";const N={class:"ds-page"},D={class:"ds-card__title"},O={class:"ds-props"},R={class:"ds-row"},S={class:"ds-controls"},M={class:"ds-row ds-row--border"},T={class:"ds-controls"},A={class:"ds-card__title"},L={class:"ds-card__title"},F={class:"variants"},H={class:"variant-item"},P={class:"variant-item"},U={class:"variant-item"},q={class:"variant-item"},J={class:"ds-card__title"},W={class:"lang-grid"},m=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,$=V({__name:"CodeBlockView",setup(j){const p=y("icon"),v=y(!1),{t:n}=h(),b={json:`{
  "id": "hh-1234567",
  "title": "Python Backend Developer",
  "salary": { "from": 180000, "to": 250000, "currency": "RUR" },
  "experience": "between3And6",
  "schedule": "remote",
  "published_at": "2026-05-17T09:00:00+05:00"
}`,typescript:`interface BlockMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

async function completeSession(sessionId: number, text: string) {
  const { data } = await api.post<BlockMessage>(\`/sessions/\${sessionId}/complete\`, { text })
  return data
}`,bash:`#!/usr/bin/env bash
set -euo pipefail
pnpm --filter web build
python build.py --clean
echo "Done: dist/release/urb-research"`,sql:`SELECT v.id, v.title, v.salary_from, c.name AS company_name
FROM hh_vacancy v
JOIN hh_company c ON c.id = v.company_id
WHERE v.status = 'active' AND v.salary_from >= 150000
ORDER BY v.published_at DESC
LIMIT 20;`};return(G,s)=>(g(),k(x,null,{default:t(()=>[a("div",N,[e(I,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),e(u,{class:"ds-card"},{default:t(()=>[a("h6",D,r(o(n)("design-system.section.code-block.props")),1),a("div",O,[a("div",R,[s[6]||(s[6]=a("span",{class:"ds-tag"},"variant",-1)),a("div",S,[e(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=c=>p.value=c),mandatory:"",divided:"",density:"compact"},{default:t(()=>[e(i,{value:"minimal"},{default:t(()=>[...s[2]||(s[2]=[d("Minimal",-1)])]),_:1}),e(i,{value:"icon"},{default:t(()=>[...s[3]||(s[3]=[d("Icon",-1)])]),_:1}),e(i,{value:"accent"},{default:t(()=>[...s[4]||(s[4]=[d("Accent",-1)])]),_:1}),e(i,{value:"compact"},{default:t(()=>[...s[5]||(s[5]=[d("Compact",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[7]||(s[7]=a("span",{class:"ds-spec"},"header template",-1))]),a("div",M,[s[10]||(s[10]=a("span",{class:"ds-tag"},"showLineNumbers",-1)),a("div",T,[e(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=c=>v.value=c),mandatory:"",divided:"",density:"compact"},{default:t(()=>[e(i,{value:!1},{default:t(()=>[...s[8]||(s[8]=[d("Off",-1)])]),_:1}),e(i,{value:!0},{default:t(()=>[...s[9]||(s[9]=[d("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[11]||(s[11]=a("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),e(u,{class:"ds-card"},{default:t(()=>[a("h6",A,r(o(n)("design-system.section.code-block.demo")),1),e(l,{code:m,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),e(u,{class:"ds-card"},{default:t(()=>[a("h6",L,r(o(n)("design-system.section.code-block.allVariants")),1),a("div",F,[a("div",H,[s[12]||(s[12]=a("span",{class:"ds-tag"},"minimal",-1)),e(l,{code:m,lang:"python",variant:"minimal"})]),a("div",P,[s[13]||(s[13]=a("span",{class:"ds-tag"},"icon",-1)),e(l,{code:m,lang:"python",variant:"icon"})]),a("div",U,[s[14]||(s[14]=a("span",{class:"ds-tag"},"accent",-1)),e(l,{code:m,lang:"python",variant:"accent"})]),a("div",q,[s[15]||(s[15]=a("span",{class:"ds-tag"},"compact — однострочный код, копирование по наведению",-1)),e(l,{code:"uv run pytest --core",lang:"bash",variant:"compact"})])])]),_:1}),e(u,{class:"ds-card"},{default:t(()=>[a("h6",J,r(o(n)("design-system.section.code-block.languages")),1),a("div",W,[(g(),w(C,null,B(b,(c,_)=>a("div",{key:_,class:"lang-item"},[e(l,{code:c,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),Z=E($,[["__scopeId","data-v-5f20a1c5"]]);export{Z as default};
