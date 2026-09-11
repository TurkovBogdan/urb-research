import{aU as _,aV as m,bA as d,aQ as f,aO as u,bp as v,bv as e,h,aN as t,bt as n,aZ as b,bn as g,aM as c,bg as i,a as S,aI as k}from"./index-DmPD8LZu.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var I=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const x={class:"section-error",role:"alert","aria-live":"polite"},y={class:"section-error__title"},B={class:"section-error__text"},E=m({__name:"SectionError",props:{error:{}},setup(o){const r=o,{t:s}=d(),a=c(()=>r.error instanceof S&&r.error.status===404),l=c(()=>a.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,A)=>(i(),f("div",x,[(i(),u(v(a.value?e(I):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),t("p",y,n(l.value),1),t("p",B,n(e(b)(o.error)),1),g(p.$slots,"actions",{},void 0,!0)]))}}),M=k(E,[["__scopeId","data-v-10bc09e0"]]);export{M as S};
