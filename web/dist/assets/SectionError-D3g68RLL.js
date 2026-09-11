import{aS as _,aT as m,by as d,aO as f,aM as u,bn as v,bt as e,f as h,aL as t,br as n,aX as S,bl as b,aK as c,be as i,a as g,aG as k}from"./index-BtmwolUh.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var y=_("outline","search-off","SearchOff",[["path",{d:"M5.039 5.062a7 7 0 0 0 9.91 9.89m1.584 -2.434a7 7 0 0 0 -9.038 -9.057",key:"svg-0"}],["path",{d:"M3 3l18 18",key:"svg-1"}]]);const x={class:"section-error",role:"alert","aria-live":"polite"},B={class:"section-error__title"},E={class:"section-error__text"},I=m({__name:"SectionError",props:{error:{}},setup(r){const o=r,{t:s}=d(),a=c(()=>o.error instanceof g&&o.error.status===404),l=c(()=>a.value?s("common.errors.section.missing"):s("common.errors.section.failed"));return(p,C)=>(i(),f("div",x,[(i(),u(v(a.value?e(y):e(h)),{class:"section-error__icon",size:40,stroke:"1.5"})),t("p",B,n(l.value),1),t("p",E,n(e(S)(r.error)),1),b(p.$slots,"actions",{},void 0,!0)]))}}),O=k(I,[["__scopeId","data-v-10bc09e0"]]);export{O as S};
