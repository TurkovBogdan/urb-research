import{aT as V,by as h,aM as k,bJ as e,aL as t,aR as a,bt as o,br as c,a4 as f,a2 as i,aQ as d,a5 as u,aO as w,bk as B,F as C,aH as x,bi as y,be as g,aG as I}from"./index-BtmwolUh.js";import{P as N}from"./PageHeader-6n3hWajG.js";import{C as l}from"./CodeBlock-C9WSmWLc.js";import"./SectionHeader-CLcXhc8W.js";import"./IconCode-BhAPfniH.js";import"./IconCopy-BMYTMgpo.js";const E={class:"ds-page"},O={class:"ds-card__title"},R={class:"ds-props"},D={class:"ds-row"},M={class:"ds-controls"},T={class:"ds-row ds-row--border"},L={class:"ds-controls"},S={class:"ds-card__title"},A={class:"ds-card__title"},F={class:"variants"},H={class:"variant-item"},P={class:"variant-item"},U={class:"variant-item"},q={class:"variant-item"},J={class:"ds-card__title"},$={class:"lang-grid"},m=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,j=V({__name:"CodeBlockView",setup(G){const p=y("icon"),v=y(!1),{t:n}=h(),b={json:`{
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
LIMIT 20;`};return(Q,s)=>(g(),k(x,null,{default:e(()=>[t("div",E,[a(N,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),a(u,{class:"ds-card"},{default:e(()=>[t("h6",O,c(o(n)("design-system.section.code-block.props")),1),t("div",R,[t("div",D,[s[6]||(s[6]=t("span",{class:"ds-tag"},"variant",-1)),t("div",M,[a(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=r=>p.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[a(i,{value:"minimal"},{default:e(()=>[...s[2]||(s[2]=[d("Minimal",-1)])]),_:1}),a(i,{value:"icon"},{default:e(()=>[...s[3]||(s[3]=[d("Icon",-1)])]),_:1}),a(i,{value:"accent"},{default:e(()=>[...s[4]||(s[4]=[d("Accent",-1)])]),_:1}),a(i,{value:"compact"},{default:e(()=>[...s[5]||(s[5]=[d("Compact",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[7]||(s[7]=t("span",{class:"ds-spec"},"header template",-1))]),t("div",T,[s[10]||(s[10]=t("span",{class:"ds-tag"},"showLineNumbers",-1)),t("div",L,[a(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=r=>v.value=r),mandatory:"",divided:"",density:"compact"},{default:e(()=>[a(i,{value:!1},{default:e(()=>[...s[8]||(s[8]=[d("Off",-1)])]),_:1}),a(i,{value:!0},{default:e(()=>[...s[9]||(s[9]=[d("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[11]||(s[11]=t("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),a(u,{class:"ds-card"},{default:e(()=>[t("h6",S,c(o(n)("design-system.section.code-block.demo")),1),a(l,{code:m,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),a(u,{class:"ds-card"},{default:e(()=>[t("h6",A,c(o(n)("design-system.section.code-block.allVariants")),1),t("div",F,[t("div",H,[s[12]||(s[12]=t("span",{class:"ds-tag"},"minimal",-1)),a(l,{code:m,lang:"python",variant:"minimal"})]),t("div",P,[s[13]||(s[13]=t("span",{class:"ds-tag"},"icon",-1)),a(l,{code:m,lang:"python",variant:"icon"})]),t("div",U,[s[14]||(s[14]=t("span",{class:"ds-tag"},"accent",-1)),a(l,{code:m,lang:"python",variant:"accent"})]),t("div",q,[s[15]||(s[15]=t("span",{class:"ds-tag"},"compact — однострочный код, копирование по наведению",-1)),a(l,{code:"uv run pytest --core",lang:"bash",variant:"compact"})])])]),_:1}),a(u,{class:"ds-card"},{default:e(()=>[t("h6",J,c(o(n)("design-system.section.code-block.languages")),1),t("div",$,[(g(),w(C,null,B(b,(r,_)=>t("div",{key:_,class:"lang-item"},[a(l,{code:r,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),ss=I(j,[["__scopeId","data-v-5f20a1c5"]]);export{ss as default};
