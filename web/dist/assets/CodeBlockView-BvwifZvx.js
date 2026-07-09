import{ak as h,aN as V,ad as k,aX as t,ac as e,ai as a,aL as o,aK as r,v as f,t as d,ah as l,w as u,af as w,aE as B,F as C,aD as y,aB as g,aa as N}from"./index-DucitkGq.js";import{_ as x}from"./PageLayout.vue_vue_type_script_setup_true_lang-BWR86Zx6.js";import{P as E}from"./PageHeader-BYf4O_Bt.js";import{C as c}from"./CodeBlock-DCPeG-aC.js";import"./IconArrowLeft-D6XlGFor.js";import"./IconCode-kIIWdYAh.js";const I={class:"ds-page"},D={class:"ds-card__title"},O={class:"ds-props"},R={class:"ds-row"},L={class:"ds-controls"},M={class:"ds-row ds-row--border"},S={class:"ds-controls"},T={class:"ds-card__title"},A={class:"ds-card__title"},F={class:"variants"},P={class:"variant-item"},U={class:"variant-item"},q={class:"variant-item"},H={class:"ds-card__title"},$={class:"lang-grid"},m=`def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`,j=h({__name:"CodeBlockView",setup(J){const p=y("icon"),v=y(!1),{t:n}=V(),b={json:`{
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
echo "Done: dist/release/hh-support-agent"`,sql:`SELECT v.id, v.title, v.salary_from, c.name AS company_name
FROM hh_vacancy v
JOIN hh_company c ON c.id = v.company_id
WHERE v.status = 'active' AND v.salary_from >= 150000
ORDER BY v.published_at DESC
LIMIT 20;`};return(K,s)=>(g(),k(x,null,{default:t(()=>[e("div",I,[a(E,{title:o(n)("design-system.page.code-block.title"),description:o(n)("design-system.page.code-block.description"),"back-to":"/design-system"},null,8,["title","description"]),a(u,{class:"ds-card"},{default:t(()=>[e("h6",D,r(o(n)("design-system.section.code-block.props")),1),e("div",O,[e("div",R,[s[5]||(s[5]=e("span",{class:"ds-tag"},"variant",-1)),e("div",L,[a(f,{modelValue:p.value,"onUpdate:modelValue":s[0]||(s[0]=i=>p.value=i),mandatory:"",divided:"",density:"compact"},{default:t(()=>[a(d,{value:"minimal"},{default:t(()=>[...s[2]||(s[2]=[l("Minimal",-1)])]),_:1}),a(d,{value:"icon"},{default:t(()=>[...s[3]||(s[3]=[l("Icon",-1)])]),_:1}),a(d,{value:"accent"},{default:t(()=>[...s[4]||(s[4]=[l("Accent",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[6]||(s[6]=e("span",{class:"ds-spec"},"header template",-1))]),e("div",M,[s[9]||(s[9]=e("span",{class:"ds-tag"},"showLineNumbers",-1)),e("div",S,[a(f,{modelValue:v.value,"onUpdate:modelValue":s[1]||(s[1]=i=>v.value=i),mandatory:"",divided:"",density:"compact"},{default:t(()=>[a(d,{value:!1},{default:t(()=>[...s[7]||(s[7]=[l("Off",-1)])]),_:1}),a(d,{value:!0},{default:t(()=>[...s[8]||(s[8]=[l("On",-1)])]),_:1})]),_:1},8,["modelValue"])]),s[10]||(s[10]=e("span",{class:"ds-spec"},"default numbering",-1))])])]),_:1}),a(u,{class:"ds-card"},{default:t(()=>[e("h6",T,r(o(n)("design-system.section.code-block.demo")),1),a(c,{code:m,lang:"python",variant:p.value,"show-line-numbers":v.value},null,8,["variant","show-line-numbers"])]),_:1}),a(u,{class:"ds-card"},{default:t(()=>[e("h6",A,r(o(n)("design-system.section.code-block.allVariants")),1),e("div",F,[e("div",P,[s[11]||(s[11]=e("span",{class:"ds-tag"},"minimal",-1)),a(c,{code:m,lang:"python",variant:"minimal"})]),e("div",U,[s[12]||(s[12]=e("span",{class:"ds-tag"},"icon",-1)),a(c,{code:m,lang:"python",variant:"icon"})]),e("div",q,[s[13]||(s[13]=e("span",{class:"ds-tag"},"accent",-1)),a(c,{code:m,lang:"python",variant:"accent"})])])]),_:1}),a(u,{class:"ds-card"},{default:t(()=>[e("h6",H,r(o(n)("design-system.section.code-block.languages")),1),e("div",$,[(g(),w(C,null,B(b,(i,_)=>e("div",{key:_,class:"lang-item"},[a(c,{code:i,lang:_,variant:"icon"},null,8,["code","lang"])])),64))])]),_:1})])]),_:1}))}}),Z=N(j,[["__scopeId","data-v-841cce8c"]]);export{Z as default};
