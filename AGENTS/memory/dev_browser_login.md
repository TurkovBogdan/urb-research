---
name: dev_browser_login
description: Dev browser login — working creds + Chrome MCP fill_form fails to sync Vuetify v-model
metadata: 
  node_type: memory
  type: reference
  originSessionId: a45d6ba6-bddd-4872-8659-c08e85e31713
---

Driving the dev SPA login (Vite :12100 → backend :12200) via the Chrome MCP:

- **Working dev creds:** stored in the local password manager / `.env` — not recorded here. (The dev DB `admin@semaphore.local` hash did NOT match `semaphore` despite `.env`, so the admin login 401s — use the personal dev account.)
- **Gotcha:** Chrome MCP `fill_form` / `fill` sets the input `.value` but does NOT reliably fire the event Vuetify's `v-model` listens to → form submits empty creds → 401 "Неверный email или пароль". Fix: set the value via the native setter + dispatch `input` + `change`:
  ```js
  const set = (el,v) => { Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); };
  ```
- DS pages scroll inside `.page-layout__content.scroll-y` (route `scroll:'y'`), NOT the window — `fullPage` screenshot won't capture below the fold; scroll that container.

Related: [[feedback_browser_isolation]].
