import{aY as _,aZ as m,bE as d,aU as f,aS as u,bt as v,bz as e,h,aR as a,bx as n,b1 as b,br as S,aQ as c,bk as i,a as k,aM as g}from"./index-CnJWcYyq.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var x=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const E={class:"section-error",role:"alert","aria-live":"polite"},y={class:"section-error__title"},B={class:"section-error__text"},I=m({__name:"SectionError",props:{error:{}},setup(r){const o=r,{t:s}=d(),t=c(()=>o.error instanceof k&&o.error.status===404),l=c(()=>t.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,C)=>(i(),f("div",E,[(i(),u(v(t.value?e(x):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),a("p",y,n(l.value),1),a("p",B,n(e(b)(r.error)),1),S(p.$slots,"actions",{},void 0,!0)]))}}),z=g(I,[["__scopeId","data-v-10bc09e0"]]);export{z as S};
