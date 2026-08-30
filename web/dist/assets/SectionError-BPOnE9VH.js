import{aP as m,aQ as _,bq as f,aL as d,aJ as u,bh as v,bn as e,e as h,aI as a,bl as n,bf as b,aH as c,b9 as i,aD as S}from"./index-DnbHu5e1.js";import{e as g,A as k}from"./internal-D4GWQcG0.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var I=m("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const x={class:"section-error",role:"alert","aria-live":"polite"},y={class:"section-error__title"},B={class:"section-error__text"},E=_({__name:"SectionError",props:{error:{}},setup(o){const r=o,{t:s}=f(),t=c(()=>r.error instanceof k&&r.error.status===404),l=c(()=>t.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,A)=>(i(),d("div",x,[(i(),u(v(t.value?e(I):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),a("p",y,n(l.value),1),a("p",B,n(e(g)(o.error)),1),b(p.$slots,"actions",{},void 0,!0)]))}}),M=S(E,[["__scopeId","data-v-10bc09e0"]]);export{M as S};
