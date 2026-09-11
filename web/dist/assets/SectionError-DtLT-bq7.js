import{aT as _,aU as m,bz as d,aP as f,aN as u,bo as v,bu as e,g as h,aM as t,bs as n,aY as b,bm as g,aL as c,bf as i,a as S,aH as k}from"./index-CAXGhYas.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var x=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const y={class:"section-error",role:"alert","aria-live":"polite"},B={class:"section-error__title"},E={class:"section-error__text"},I=m({__name:"SectionError",props:{error:{}},setup(o){const r=o,{t:s}=d(),a=c(()=>r.error instanceof S&&r.error.status===404),l=c(()=>a.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,C)=>(i(),f("div",y,[(i(),u(v(a.value?e(x):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),t("p",B,n(l.value),1),t("p",E,n(e(b)(o.error)),1),g(p.$slots,"actions",{},void 0,!0)]))}}),T=k(I,[["__scopeId","data-v-10bc09e0"]]);export{T as S};
