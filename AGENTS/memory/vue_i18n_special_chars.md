---
name: vue_i18n_special_chars
description: "vue-i18n message syntax — literal @ and | break compilation; escape with {'@'} / {'|'}"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3b7a355f-14fa-41a1-8616-ce8c6fe605f0
---

vue-i18n (v9, used via Vuetify adapter — see [[i18n_frontend_setup]]) parses message strings: `@` starts a **linked message** (`@:key`) and `|` separates **plural forms**. A locale value containing a literal `@` (e.g. an email example) throws `SyntaxError: Message compilation error: Invalid linked format` at render; a literal `|` silently splits the string into plural forms (only the first shows).

Escape both with literal interpolation: `service{'@'}paypal.com`, `a{'|'}b`. First hit: `mail_sync` `filters.dialog.rule_ph` placeholder (`e.g. no-?reply|not[_-]reply or service@paypal.com`) — error only surfaced when the add/edit filter dialog opened. When auditing locales for this, grep for `[a-z0-9]@[a-z]` and bare `|` in message values.
