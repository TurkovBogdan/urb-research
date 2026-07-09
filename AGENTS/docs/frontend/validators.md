# Frontend — input validators

Pure validation helpers for Vuetify form fields. Lives in `web/src/shared/utils/validators.ts`.

## Contract

Each validator is a **factory** returning a Vuetify rule — a function `(v: unknown) => true | string`. `true` means valid; a string is the error message shown by the field.

```ts
type Rule = (v: unknown) => true | string
```

Factories accept an optional custom message so callers can override the default text without forking the logic.

```ts
import { isSlug } from '@/shared/utils/validators'

const rules = [isSlug()]                    // default message
const rules = [isSlug('Только латиница')]   // custom message
```

In a template:

```vue
<VTextField v-model="code" :rules="[isSlug()]" />
```

## Why factories, not plain functions

Vuetify passes the value to each rule on every input event. If the rule needs parameters (min length, allowed pattern, custom message), the rule itself must be a closure that already captured them. The factory pattern keeps the call site clean:

```ts
:rules="[minLength(3), isSlug()]"      // factories
:rules="[(v) => minLength(v, 3), …]"   // ugly without factories
```

## Empty values

Validators **pass empty strings / `null` / `undefined`** by default. Pair with a separate `required()` rule if the field must be filled — this keeps the «format» and «presence» checks composable.

```ts
:rules="[required(), isSlug()]"
```

## Current exports

| Export | Kind | Purpose |
|---|---|---|
| `isSlug(msg?)` | rule factory | allows `a-z`, `0-9`, `-`, `_` (no spaces/uppercase/other punctuation). Default msg: `Только a-z, 0-9, дефис и подчёркивание` |

> The `minLength`/`required` names used in the examples above are illustrative — they are **not** exported here; compose your own or use Vuetify's.

## Adding new validators

Add the factory to `web/src/shared/utils/validators.ts`. Keep each factory:

- pure — no `ref`, no `import` of components or stores
- self-contained — one regex / one comparison, no chaining other validators inside
- forgiving on empty values — return `true` for `''` / `null` / `undefined`

If a validator grows beyond a one-liner regex (async checks, network calls, cross-field comparisons), it does not belong here — put it next to the form that needs it, or in `composables/`.
