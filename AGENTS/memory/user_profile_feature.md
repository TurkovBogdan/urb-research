---
name: user_profile_feature
description: "Frontend user-profile feature — /profile self-edit page + sidebar profile component (name → profile, logout button)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7919dbd3-1e91-485b-af2b-3526d76ded8d
---

Frontend `web/src/features/user-profile/` (shipped 2026-06-05, task `2026-06-05-core-users-self-guard-name`).

- **`/profile`** route — auth-only, NO level gate (`meta: { scroll: 'y' }`; any logged-in user sees their own). `views/ProfileView.vue` edits **name + bio** («О себе»/role, `VTextarea` ≤256, optional) via `api.updateProfile(userId, name, bio)` → `PATCH /core-users/users/{id}` (the backend `self`-guarded route; email is shown read-only in the card head only, NOT a form field; password out-of-scope). On success calls `auth.setUser(updated)` (new store action = `_apply` exposed) to refresh the cached principal + rebuild CASL.
- **`components/ProfileNavCard.vue`** — lives in the feature but is **rendered by the layout** (`AppSidebar` `#append`, pinned at the very bottom, after locale/clock). Cross-layer import is fine (AppSidebar already imports feature navs). It **owns logout** (`auth.logout()` → `router.push('/login')`) — the old standalone logout `VListItem`/`onLogout` were removed from `AppSidebar`, and `IconLogout` import dropped there. Expanded: avatar-initial + name (click → `/profile`) + role line, logout icon-btn on the right. Collapsed rail (56px): stacked avatar + logout, both `sidebar-tooltip`'d. Self-styled (does NOT reuse AppSidebar's scoped `.nav-item` classes).
- `UserView` type (`api/auth.ts`) gained `name`; namespace `user-profile` (hyphen, like `design-system`) glob-registered from `locales/{ru,en}.json`. Role labels = `user-profile.level.<group>`.

Backend contract behind it: [[core_users_module]] (`name` field + `self` guard). See also [[frontend_rules]] / [[clickable_card_default]].
