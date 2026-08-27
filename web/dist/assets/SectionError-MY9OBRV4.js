import{aH as m,aI as _,be as d,aD as f,aB as u,b5 as v,bb as e,b as h,aA as a,b9 as n,b3 as b,az as c,aZ as i,av as S}from"./index-Ck6Fpicj.js";import{e as g,A as k}from"./internal-BItLbylK.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var B=m("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const I={class:"section-error",role:"alert","aria-live":"polite"},x={class:"section-error__title"},y={class:"section-error__text"},A=_({__name:"SectionError",props:{error:{}},setup(o){const r=o,{t:s}=d(),t=c(()=>r.error instanceof k&&r.error.status===404),l=c(()=>t.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,E)=>(i(),f("div",I,[(i(),u(v(t.value?e(B):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),a("p",x,n(l.value),1),a("p",y,n(e(g)(o.error)),1),b(p.$slots,"actions",{},void 0,!0)]))}}),z=S(A,[["__scopeId","data-v-10bc09e0"]]);export{z as S};
