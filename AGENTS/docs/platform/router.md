# router.md — зоны, регистрация маршрутов, guard'ы

Как модуль отдаёт HTTP-маршруты ядру, как они защищаются (`@guard` + реестр) и какие
параметры есть. Это **реализованный** референс (код в `src/core/router/`,
`src/core/app_factory.py`). История решений — план `AGENTS/plans/2026-06-03-api-zones.md`.

## Зоны

HTTP делится на зоны = префиксное пространство роутеров поверх общего реестра guard'ов.

| Зона | Префикс | Статус | Идентичность (цель) |
|------|---------|--------|---------------------|
| internal | `/internal` | **активна** | сессия-cookie (SPA + auth) — guard даст будущий auth-модуль |
| api | `/api` | болванка (`router/api.py`), не смонтирована | внешний токен + scope |
| webhook | `/webhook` | болванка (`router/webhook.py`), не смонтирована | подпись источника |
| mcp | `/mcp` | **подключена** (пуста — ждёт `mcp_router` + guard `token`) | per-user bearer-токен (тип `mcp`) |

> **mcp — 4-я зона** (публичный MCP-раздел). Отдельная зона, а не часть `api`: своя
> идентичность — долгоживущий bearer-токен, привязанный к пользователю и типизированный
> (`type=mcp`), со своим умолчательным guard'ом (вид `token`), не пересекается с `scope`-
> семантикой будущего внешнего `api`. Зона **уже заведена и подключена к `create_app`**
> (`router/mcp.py`: `MCP_PREFIX="/mcp"`, `MCP_DEFAULT_GUARDS=["token"]`, `build_mcp_zone`;
> classvar'ы `Module.mcp_router`/`mcp_router_prefix`). В отличие от болванок `api`/`webhook`
> она монтируется автоматически — но **только при непустой зоне** (когда модуль дал
> `mcp_router`): пустую не монтируем, иначе `validate_guard_rules` упала бы на ещё не
> существующем default-guard `token`. Остаётся реализовать guard `token` (будущий auth-модуль) +
> модульный `mcp_router`.

Зону отличают только **префикс** + её **умолчательный список видов** (`default`, см. ниже).
Сами guard'ы зону не знают — реестр один на все зоны. Монтаж — в `mount_router_zones`
(`src/core/router/mounting.py`), который `create_app` зовёт под гейтом `SERVER_ENABLED`;
зона собирается СВЕЖЕЙ на каждый вызов (без глобального синглтона).

**Health:** `GET /internal/health` — публичный (`@guard("allow_all")`) liveness ВНУТРИ зоны
(`_health` в `src/core/router/internal.py`). Доступен только при смонтированной зоне ⇒ отражает,
что API реально поднят: `SERVER_ENABLED=true` → `200 {"status":"ok"}`; `false` → нет
маршрута (404). Отдельного always-on `/api/health` больше нет.

## Регистрация маршрутов модулем

Модуль отдаёт роутер декларативно — НЕ монтирует сам в `configure`:

```python
# src/modules/<m>/module.py
from src.modules.<m>.api import router

class XModule(Module):
    name = "x"
    internal_router = router          # APIRouter модуля (см. .api)
    internal_router_prefix = "/x"              # под-префикс В ЗОНЕ; не выводится из name (kebab vs underscore)

    def configure(self, app, config):
        register_tasks()              # scheduler-задачи/прочая логика — остаётся здесь
```

`create_app` агрегирует `internal_router` каждого модуля в зону internal (через
`build_internal_zone`, `src/core/router/internal.py`):
`zone.include_router(m.internal_router, prefix=m.internal_router_prefix, tags=[m.name])`, затем
монтирует зону на `/internal` с зон-guard'ом. Итог: `/internal/<internal_router_prefix>/...`.

`configure(app, config)` выполняется **всегда** (и при выключенном API) — там регистрируют
scheduler-задачи и sync-ресурсы; **монтаж роутеров туда не кладут** (его делает зона под флагом).

**Параметры `Module` (контракт роутинга):**

| Атрибут | Тип | По умолчанию | Назначение |
|---------|-----|--------------|------------|
| `guards` | `dict[str, GuardFn]` | `{}` | виды guard'ов модуля (`вид → GuardFn`); ядро вливает в реестр (см. ниже). Объявляется ДО роутеров — защита прежде защищаемой поверхности |
| `internal_router` | `APIRouter \| None` | `None` | под-роутер зоны internal; `None` — модуль без HTTP |
| `internal_router_prefix` | `str` | `""` | под-префикс в зоне (напр. `"/my-module"`) |

## Метка `@guard` — защита маршрута

`@guard("вид", *аргументы)` (`src/core/router/guards/enforce.py`) навешивает на функцию-эндпоинт
**непрозрачные данные** — кортеж `(вид, *аргументы)` в `fn.__guards__`. Ядро вид/аргументы
НЕ парсит (кроме встроенных `allow_all`/`deny_all`); смысл реализует guard из реестра.

```python
from src.core.router import guard

@router.get("/items")                            # без метки ⇒ умолчание зоны (allow_all)
async def list_items(): ...

@router.post("/items")
@guard("allow_all")                              # явно публичный
async def create_item(): ...

@router.delete("/items/{id}")
@guard("deny_all")                               # явно «погасить» маршрут
async def delete_item(): ...
```

**Параметры `@guard(kind, *args)`:**
- `kind: str` — вид guard'а; должен быть зарегистрирован в реестре (иначе ошибка на старте).
- `*args: str` — аргументы для guard'а этого вида (смысл аргументов определяет сам guard).
- Метку можно вешать **несколько раз** — правила накапливаются (читается `guard_rules(ep)`).
- Порядок декораторов: `@guard(...)` ставится МЕЖДУ `@router.get(...)` и `async def`.

**Встроенные виды (знает само ядро):**

| Вид | Функция | Эффект |
|-----|---------|--------|
| `allow_all` | `guard_allow_all` | пропускает всех (снимает умолчание зоны) |
| `deny_all` | `guard_deny_all` | блокирует всех (явно «погасить» маршрут); он же фолбэк |

> Это **все** встроенные в bare-core виды. Auth-виды (`auth`/`ability`/`self`/`token_owner` с
> метками `<уровень>:<действие>`) в bare-core не зарегистрированы —
> их даст будущий auth-модуль через декларативный `Module.guards`.

## Как защита исполняется (`zone_guard`)

Зона монтируется с зависимостью `make_zone_guard(registry, default=["allow_all"])`. На каждый
запрос (`src/core/router/guards/enforce.py`):

```
endpoint = request.scope["endpoint"]
if @guard("allow_all") → allow_all (всё разрешает) и выход
if @guard("deny_all")  → deny_all  (всё кладёт) и выход
kinds = default(зоны) + виды меток endpoint'а         # напр. ["allow_all"] + [...]
for kind in kinds or ["deny_all"]:                    # пусто ⇒ deny_all (фолбэк)
    await registry.resolve(kind)(request)             # по порядку; первый raise останавливает
```

- **Default-on**: умолчание зоны применяется к каждому маршруту без `allow_all`/`deny_all`.
  В bare-core умолчание `internal` — `allow_all` (нет auth-модуля); когда он появится, умолчание
  станет вид `auth` и маршрут без `@guard` ⇒ только `auth`.
- **`request.state.user`**: будущий `auth`-guard кладёт пользователя сюда; последующие guard'ы и
  хендлер читают его. Прерывание — `raise ApiError` (→ стандартный JSON).
- **«Пусто» ⇒ `deny_all`**: если у маршрута не набралось ни умолчания зоны, ни меток — закрыт
  (secure-by-default). Это про ЗОНУ без умолчания/реестра, не про «нет меток» само по себе.

`default` — параметр МОНТАЖА зоны (не свойство реестра): bare-core `internal`→`["allow_all"]`
(будущий auth-модуль сменит на `["auth"]`), позже `api`→`["scope"]`, `webhook`→`["signature"]`,
`mcp`→`["token"]`.

## Реестр guard'ов

Один общий (не зонный) реестр `вид → guard` (`src/core/router/guards/registry.py`):

| Метод | Назначение |
|-------|------------|
| `add(kind, fn)` | зарегистрировать; повторный `add` того же вида ⇒ `ValueError` |
| `has(kind) -> bool` | есть ли вид |
| `resolve(kind) -> GuardFn` | получить реализацию |

`GuardFn` = `async (request: Request) -> None`, прерывает через `raise ApiError`. Имя
функции-реализации = `guard_` + вид (`guard_allow_all`, `guard_auth`, …).

Реестр собирается в `build_guard_registry` (`src/core/router/mounting.py`): ядро
предрегистрирует `allow_all`/`deny_all`, затем вливает декларативный `Module.guards`
каждого модуля (`registry.add` — в ядре). Строится один раз при сборке, дальше не
мутируется (НЕ рантайм-реестр).

**Модуль объявляет свои виды декларативно (атрибутом, как `internal_router`):**

```python
class MyModule(Module):
    guards = {
        "my_guard": guard_my_guard,
    }
```

**Валидация на сборке** (`validate_guard_rules`, вызывается в `mount_router_zones` после монтажа каждой зоны):
все виды в `@guard(...)` на маршрутах + умолчательные виды зоны должны быть в реестре, иначе
`RuntimeError` на старте. Декоратор проверить не может (отрабатывает при импорте, до реестра).

## middleware ≠ guard

- **guard** = наше прозвище для FastAPI-**зависимости** доступа (`Depends`), пост-роутинг,
  видит endpoint и метки, прерывается `raise`. Все `@guard`/`auth`/`ability` — это guard'ы.
- **middleware** = сквозная ASGI-логика (`src/core/middleware/`), до роутинга, на каждый
  запрос, endpoint не видит — для логирования/CORS/rate-limit/request-id, НЕ для per-route
  auth. Метку `@guard` снять per-route может только зависимость, не middleware.

## Флаг `SERVER_ENABLED` — глобальный гейт API

`Config.server_enabled` (env `SERVER_ENABLED`). **Глобальный** выключатель всего, что
связано с HTTP-API:

- `false` (**дефолт в коде**) — НИЧЕГО API не поднимается: ни зон/маршрутов, ни `/internal/health`,
  ни CORS — **0 HTTP-маршрутов**. Процесс в режиме «только worker» (lifespan: DB/миграции/модули/
  scheduler как обычно). Гейт в двух местах: `create_app` (зоны) и `apps/app/server.py` (CORS).
- `true` — зона internal монтируется и обслуживается + CORS. dev `.env` = `true`. Статику фронта
  раздаёт nginx (prod) или Vite (dev) — backend всегда API-only.

**Swagger/OpenAPI выключены всегда** (`docs_url`/`openapi_url`/`redoc_url=None` в `create_app`): API
внутренний, схему наружу не публикуем — независимо от флага.

CLI перекрывает env: `src/app.py --backend`/`--no-backend` (плюс `--host`/`--port`/`--processes`).
Флаг выставляется в `os.environ` ДО `Config()`/импорта приложения → наследуется reload/processes-
подпроцессами uvicorn. Приоритет: **флаг > env > дефолт `false`**. Полный список флагов и роль
SERVER/WORKER — в [`dev/docs/ENV.md`](../../../dev/docs/ENV.md).

## Текущее состояние

- Активна зона **internal** (`/internal`); `api`/`webhook` — болванки (отключены).
- Зона **mcp** (`/mcp`, 4-я) **заведена и подключена** к `create_app` (`router/mcp.py` +
  classvar'ы `Module.mcp_router`/`mcp_router_prefix`), но монтируется лишь при непустой зоне
  (пока ни один модуль не дал `mcp_router` ⇒ не смонтирована). Остаётся guard-вид `token`
  (его даст будущий auth-модуль вместе с per-user токенами) + модульный `mcp_router`.
- **Bare-core: auth-модуля нет.** Ядро держит только `allow_all`/`deny_all`; видов
  `auth`/`ability` сейчас нет в реестре. Поэтому умолчание зоны internal — `allow_all`
  (а не `auth`); их вернёт будущий auth-модуль через `Module.guards` (и тогда умолчание
  можно сменить на `auth`).
- URL уже `/internal/...`; фронт ходит туда (`web/src/features/*/api.ts`, vite-прокси `/internal`).

## Как добавить новый вид guard'а

1. Написать функцию `async def guard_<вид>(request) -> None` (raise при отказе; имя = `guard_` + вид).
2. Объявить в `Module.guards`: `guards = {"мой_вид": guard_мой_вид}`.
3. Вешать на маршруты `@guard("мой_вид", ...args)`. Валидация на старте проверит наличие.
4. Если вид читает аргументы — брать их из `guard_rules(request.scope["endpoint"])` по своему `kind`.

## Карта файлов

```
src/core/router/guards/registry.py    # GuardRegistry (add/has/resolve) + тип GuardFn
src/core/router/guards/universal.py   # встроенная пара guard_allow_all (всё разрешает) / guard_deny_all (всё кладёт + фолбэк)
src/core/router/guards/enforce.py     # @guard, guard_rules, is_allow_all/is_deny_all, make_zone_guard, validate_guard_rules
src/core/router/guards/__init__.py    # реэкспорт guard-поверхности (реестр + built-in'ы + метки) единой точкой
src/core/router/internal.py   # build_internal_zone (состав зоны internal) + /health + INTERNAL_PREFIX/DEFAULT_GUARDS
src/core/router/api.py        # БОЛВАНКА зоны api (/api): build_api_zone + API_PREFIX/DEFAULT_GUARDS (scope) — не смонтирована
src/core/router/webhook.py    # БОЛВАНКА зоны webhook (/webhook): build_webhook_zone + WEBHOOK_PREFIX/DEFAULT_GUARDS (signature) — не смонтирована
src/core/router/mcp.py        # зона mcp (/mcp): build_mcp_zone + MCP_PREFIX/DEFAULT_GUARDS (token) — ПОДКЛЮЧЕНА в create_app, монтаж при непустой зоне; guard token + mcp_router ещё впереди
src/core/router/__init__.py   # реэкспорт реестра/built-in'ов/меток (зону собирает internal.py)
src/core/module.py            # Module.internal_router / internal_router_prefix / mcp_router / mcp_router_prefix / guards (декларативно)
src/core/router/mounting.py   # build_guard_registry + mount_router_zones (монтаж зон + валидация); условия подключения каждой зоны — здесь, явно
src/core/app_factory.py       # create_app: гейт SERVER_ENABLED → зовёт mount_router_zones (сам монтаж вынесен в router/mounting.py)
src/core/config.py            # Config.server_enabled
src/app.py            # CLI-вход (--backend/--worker)
```
