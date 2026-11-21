import{aZ as V,bE as h,aS as k,bP as e,aR as a,aX as t,bz as o,bx as c,a8 as f,a6 as i,aW as d,a9 as u,aU as w,bq as B,F as C,aN as x,bo as y,bk as g,aM as N}from"./index-CnJWcYyq.js";import{P as E}from"./PageHeader-Dksx1iPs.js";import{C as l}from"./CodeBlock-eqHTnwo5.js";import"./SectionHeader-CzhT1HEK.js";import"./IconCode-C-ec_W9I.js";import"./IconCopy-CFz-agQ0.js";const I={class:"ds-page"},R={class:"ds-card__title"},D={class:"ds-props"},M={class:"ds-row"},O={class:"ds-controls"},S={class:"ds-row ds-row--border"},T={class:"ds-controls"},A={class:"ds-card__title"},L={class:"ds-card__title"},P={class:"variants"},U={class:"variant-item"},q={class:"variant-item"},F={class:"variant-item"},H={class:"variant-item"},W={class:"ds-card__title"},$={class:"lang-grid"},m=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,j=V({__name:"CodeBlockView",setup(z){const p=y("icon"),v=y(!1),{t:n}=h(),b={json:`{
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
LIMIT 20;`};return(J,s)=>(g(),k(x,null,{default:e(()=>[a("div",I,[t(E,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),t(u,{class:"ds-card"},{default:e(()=>[a("h6",R,c(o(n)("design-system.section.code-block.props")),1),a("div",D,[a("div",M,[s[6]||(s[6]=a("span",{class:"ds-tag"},"variant",-1)),a("div",O,[t(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=r=>p.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[t(i,{value:"minimal"},{default:e(()=>[...s[2]||(s[2]=[d("Minimal",-1)])]),_:1}),t(i,{value:"icon"},{default:e(()=>[...s[3]||(s[3]=[d("Icon",-1)])]),_:1}),t(i,{value:"accent"},{default:e(()=>[...s[4]||(s[4]=[d("Accent",-1)])]),_:1}),t(i,{value:"compact"},{default:e(()=>[...s[5]||(s[5]=[d("Compact",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[7]||(s[7]=a("span",{class:"ds-spec"},"header template",-1))]),a("div",S,[s[10]||(s[10]=a("span",{class:"ds-tag"},"showLineNumbers",-1)),a("div",T,[t(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=r=>v.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[t(i,{value:!1},{default:e(()=>[...s[8]||(s[8]=[d("Off",-1)])]),_:1}),t(i,{value:!0},{default:e(()=>[...s[9]||(s[9]=[d("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[11]||(s[11]=a("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),t(u,{class:"ds-card"},{default:e(()=>[a("h6",A,c(o(n)("design-system.section.code-block.demo")),1),t(l,{code:m,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),t(u,{class:"ds-card"},{default:e(()=>[a("h6",L,c(o(n)("design-system.section.code-block.allVariants")),1),a("div",P,[a("div",U,[s[12]||(s[12]=a("span",{class:"ds-tag"},"minimal",-1)),t(l,{code:m,lang:"python",variant:"minimal"})]),a("div",q,[s[13]||(s[13]=a("span",{class:"ds-tag"},"icon",-1)),t(l,{code:m,lang:"python",variant:"icon"})]),a("div",F,[s[14]||(s[14]=a("span",{class:"ds-tag"},"accent",-1)),t(l,{code:m,lang:"python",variant:"accent"})]),a("div",H,[s[15]||(s[15]=a("span",{class:"ds-tag"},"compact — однострочный код, копирование по наведению",-1)),t(l,{code:"uv run pytest --core",lang:"bash",variant:"compact"})])])]),_:1}),t(u,{class:"ds-card"},{default:e(()=>[a("h6",W,c(o(n)("design-system.section.code-block.languages")),1),a("div",$,[(g(),w(C,null,B(b,(r,_)=>a("div",{key:_,class:"lang-item"},[t(l,{code:r,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),ss=N(j,[["__scopeId","data-v-5f20a1c5"]]);export{ss as default};
