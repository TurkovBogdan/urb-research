import{aP as r,b8 as s,bc as u}from"./index-DgoYO1jO.js";/**
 * @license @tabler/icons-vue v3.44.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var p=r("outline","dots-vertical","DotsVertical",[["path",{d:"M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-0"}],["path",{d:"M11 19a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-1"}],["path",{d:"M11 5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-2"}]]);function m(c=1800){const a=u(null);let o;function n(e){const t=document.createElement("textarea");t.value=e,t.style.cssText="position:fixed;top:-9999px;left:-9999px;opacity:0",document.body.appendChild(t),t.focus(),t.select(),document.execCommand("copy"),document.body.removeChild(t)}async function i(e){try{await navigator.clipboard.writeText(e)}catch{n(e)}a.value=e,clearTimeout(o),o=setTimeout(()=>{a.value=null},c)}const l=e=>a.value===e;return s(()=>clearTimeout(o)),{copiedText:a,copy:i,isCopied:l}}export{p as I,m as u};
