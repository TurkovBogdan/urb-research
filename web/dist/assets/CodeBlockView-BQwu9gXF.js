import{aV as V,bA as h,aO as k,bL as e,aN as t,aT as a,bv as o,bt as c,a6 as f,a4 as i,aS as d,a7 as m,aQ as w,bm as B,F as C,aJ as I,bk as g,bg as y,aI as N}from"./index-DmPD8LZu.js";import{P as x}from"./PageHeader-Bm2NrN2b.js";import{C as l}from"./CodeBlock-D1gc1QtM.js";import"./SectionHeader-R3U805Ya.js";import"./IconCode-DpyLWJm_.js";import"./IconCopy-Dm2JOzNK.js";const E={class:"ds-page"},O={class:"ds-card__title"},D={class:"ds-props"},R={class:"ds-row"},S={class:"ds-controls"},T={class:"ds-row ds-row--border"},A={class:"ds-controls"},L={class:"ds-card__title"},M={class:"ds-card__title"},F={class:"variants"},P={class:"variant-item"},U={class:"variant-item"},q={class:"variant-item"},H={class:"variant-item"},J={class:"ds-card__title"},$={class:"lang-grid"},u=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,j=V({__name:"CodeBlockView",setup(Q){const p=g("icon"),v=g(!1),{t:n}=h(),b={json:`{
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
LIMIT 20;`};return(W,s)=>(y(),k(I,null,{default:e(()=>[t("div",E,[a(x,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),a(m,{class:"ds-card"},{default:e(()=>[t("h6",O,c(o(n)("design-system.section.code-block.props")),1),t("div",D,[t("div",R,[s[6]||(s[6]=t("span",{class:"ds-tag"},"variant",-1)),t("div",S,[a(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=r=>p.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[a(i,{value:"minimal"},{default:e(()=>[...s[2]||(s[2]=[d("Minimal",-1)])]),_:1}),a(i,{value:"icon"},{default:e(()=>[...s[3]||(s[3]=[d("Icon",-1)])]),_:1}),a(i,{value:"accent"},{default:e(()=>[...s[4]||(s[4]=[d("Accent",-1)])]),_:1}),a(i,{value:"compact"},{default:e(()=>[...s[5]||(s[5]=[d("Compact",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[7]||(s[7]=t("span",{class:"ds-spec"},"header template",-1))]),t("div",T,[s[10]||(s[10]=t("span",{class:"ds-tag"},"showLineNumbers",-1)),t("div",A,[a(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=r=>v.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[a(i,{value:!1},{default:e(()=>[...s[8]||(s[8]=[d("Off",-1)])]),_:1}),a(i,{value:!0},{default:e(()=>[...s[9]||(s[9]=[d("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[11]||(s[11]=t("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),a(m,{class:"ds-card"},{default:e(()=>[t("h6",L,c(o(n)("design-system.section.code-block.demo")),1),a(l,{code:u,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),a(m,{class:"ds-card"},{default:e(()=>[t("h6",M,c(o(n)("design-system.section.code-block.allVariants")),1),t("div",F,[t("div",P,[s[12]||(s[12]=t("span",{class:"ds-tag"},"minimal",-1)),a(l,{code:u,lang:"python",variant:"minimal"})]),t("div",U,[s[13]||(s[13]=t("span",{class:"ds-tag"},"icon",-1)),a(l,{code:u,lang:"python",variant:"icon"})]),t("div",q,[s[14]||(s[14]=t("span",{class:"ds-tag"},"accent",-1)),a(l,{code:u,lang:"python",variant:"accent"})]),t("div",H,[s[15]||(s[15]=t("span",{class:"ds-tag"},"compact — однострочный код, копирование по наведению",-1)),a(l,{code:"uv run pytest --core",lang:"bash",variant:"compact"})])])]),_:1}),a(m,{class:"ds-card"},{default:e(()=>[t("h6",J,c(o(n)("design-system.section.code-block.languages")),1),t("div",$,[(y(),w(C,null,B(b,(r,_)=>t("div",{key:_,class:"lang-item"},[a(l,{code:r,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),ss=N(j,[["__scopeId","data-v-5f20a1c5"]]);export{ss as default};
