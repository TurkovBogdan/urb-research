import{aQ as V,bq as h,aJ as k,bB as a,aI as e,aO as t,bn as o,bl as c,a1 as f,$ as i,aN as d,a2 as u,aL as B,be as w,F as C,aE as I,bc as y,b9 as g,aD as N}from"./index-DgoYO1jO.js";import{P as x}from"./PageHeader-C93-h_jI.js";import{C as l}from"./CodeBlock-CLVloEAm.js";import"./SectionHeader-C_w2_1Y4.js";import"./IconCode-C8qU1hKt.js";import"./IconCopy-DwcYywh9.js";const E={class:"ds-page"},D={class:"ds-card__title"},O={class:"ds-props"},R={class:"ds-row"},L={class:"ds-controls"},M={class:"ds-row ds-row--border"},S={class:"ds-controls"},T={class:"ds-card__title"},A={class:"ds-card__title"},q={class:"variants"},F={class:"variant-item"},P={class:"variant-item"},U={class:"variant-item"},$={class:"variant-item"},H={class:"ds-card__title"},J={class:"lang-grid"},m=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,j=V({__name:"CodeBlockView",setup(Q){const p=y("icon"),v=y(!1),{t:n}=h(),b={json:`{
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
LIMIT 20;`};return(W,s)=>(g(),k(I,null,{default:a(()=>[e("div",E,[t(x,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),t(u,{class:"ds-card"},{default:a(()=>[e("h6",D,c(o(n)("design-system.section.code-block.props")),1),e("div",O,[e("div",R,[s[6]||(s[6]=e("span",{class:"ds-tag"},"variant",-1)),e("div",L,[t(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=r=>p.value=r),mandatory:"",divided:"",density:"compact"},{default:a(()=>[t(i,{value:"minimal"},{default:a(()=>[...s[2]||(s[2]=[d("Minimal",-1)])]),_:1}),t(i,{value:"icon"},{default:a(()=>[...s[3]||(s[3]=[d("Icon",-1)])]),_:1}),t(i,{value:"accent"},{default:a(()=>[...s[4]||(s[4]=[d("Accent",-1)])]),_:1}),t(i,{value:"compact"},{default:a(()=>[...s[5]||(s[5]=[d("Compact",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[7]||(s[7]=e("span",{class:"ds-spec"},"header template",-1))]),e("div",M,[s[10]||(s[10]=e("span",{class:"ds-tag"},"showLineNumbers",-1)),e("div",S,[t(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=r=>v.value=r),mandatory:"",divided:"",density:"compact"},{default:a(()=>[t(i,{value:!1},{default:a(()=>[...s[8]||(s[8]=[d("Off",-1)])]),_:1}),t(i,{value:!0},{default:a(()=>[...s[9]||(s[9]=[d("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[11]||(s[11]=e("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),t(u,{class:"ds-card"},{default:a(()=>[e("h6",T,c(o(n)("design-system.section.code-block.demo")),1),t(l,{code:m,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),t(u,{class:"ds-card"},{default:a(()=>[e("h6",A,c(o(n)("design-system.section.code-block.allVariants")),1),e("div",q,[e("div",F,[s[12]||(s[12]=e("span",{class:"ds-tag"},"minimal",-1)),t(l,{code:m,lang:"python",variant:"minimal"})]),e("div",P,[s[13]||(s[13]=e("span",{class:"ds-tag"},"icon",-1)),t(l,{code:m,lang:"python",variant:"icon"})]),e("div",U,[s[14]||(s[14]=e("span",{class:"ds-tag"},"accent",-1)),t(l,{code:m,lang:"python",variant:"accent"})]),e("div",$,[s[15]||(s[15]=e("span",{class:"ds-tag"},"compact — однострочный код, копирование по наведению",-1)),t(l,{code:"uv run pytest --core",lang:"bash",variant:"compact"})])])]),_:1}),t(u,{class:"ds-card"},{default:a(()=>[e("h6",H,c(o(n)("design-system.section.code-block.languages")),1),e("div",J,[(g(),B(C,null,w(b,(r,_)=>e("div",{key:_,class:"lang-item"},[t(l,{code:r,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),ss=N(j,[["__scopeId","data-v-5f20a1c5"]]);export{ss as default};
