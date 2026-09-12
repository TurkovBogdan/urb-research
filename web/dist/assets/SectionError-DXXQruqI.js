import{aW as _,aX as m,bC as d,aS as f,aQ as u,br as v,bx as e,h,aP as t,bv as n,a$ as S,bp as b,aO as c,bi as i,a as g,aK as k}from"./index-CLJuoddt.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var x=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const y={class:"section-error",role:"alert","aria-live":"polite"},B={class:"section-error__title"},C={class:"section-error__text"},E=m({__name:"SectionError",props:{error:{}},setup(r){const o=r,{t:s}=d(),a=c(()=>o.error instanceof g&&o.error.status===404),l=c(()=>a.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,I)=>(i(),f("div",y,[(i(),u(v(a.value?e(x):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),t("p",B,n(l.value),1),t("p",C,n(e(S)(r.error)),1),b(p.$slots,"actions",{},void 0,!0)]))}}),A=k(E,[["__scopeId","data-v-10bc09e0"]]);export{A as S};
