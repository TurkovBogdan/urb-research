import{aI as _,aJ as m,bf as f,aE as d,aC as u,b6 as v,bc as e,b as h,aB as t,ba as c,b4 as b,aA as n,a_ as i,aw as S}from"./index-Ds9idVhQ.js";import{e as g,A as k}from"./internal-BOeJu1ex.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var B=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const E={class:"section-error",role:"alert","aria-live":"polite"},I={class:"section-error__title"},x={class:"section-error__text"},y=m({__name:"SectionError",props:{error:{}},setup(o){const r=o,{t:s}=f(),a=n(()=>r.error instanceof k&&r.error.status===404),l=n(()=>a.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,A)=>(i(),d("div",E,[(i(),u(v(a.value?e(B):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),t("p",I,c(l.value),1),t("p",x,c(e(g)(o.error)),1),b(p.$slots,"actions",{},void 0,!0)]))}}),M=S(y,[["__scopeId","data-v-10bc09e0"]]);export{M as S};
