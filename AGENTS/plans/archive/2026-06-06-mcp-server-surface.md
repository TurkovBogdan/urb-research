---
title: Поверхность MCP-серверов (на форке) — модули как MCP-серверы под /mcp
date: 2026-06-06
status: completed
description: "Отдаём модули проекта как MCP-серверы под единой базой /mcp; модуль декларирует свои серверы словарём mcp_servers (code → конструктор mcp_server), каждый монтируется как отдельное FastMCP-приложение (standalone-форк) по Streamable-HTTP. Auth — McpServerTokenVerifier (scope=mcp), потому что FastAPI зон-guard не действует на смонтированные ASGI-приложения. team первым, полный CRUD. Сторона client (llm_providers) и server (этот план) разведены по именам."
tags: [mcp, core, team, fastmcp]
---

## Цель

Раздел `/mcp` отдаёт модули проекта как MCP-серверы поверх Streamable HTTP: модуль
декларирует свои серверы словарём `mcp_servers` (`code` → конструктор), каждый монтируется
как отдельное FastMCP-приложение по адресу `/mcp/<code>` (напр. `/mcp/team`), с полным
CRUD-набором инструментов, защищённое единым `McpServerTokenVerifier`. `team` выходит
первым как эталонный сервер. Каркас сервера — standalone-форк `fastmcp`; его лишний вес
(~13 МБ) платится только в backend-процессе и только когда включена API-поверхность.

## Контекст

- Старые in-process MCP-приложения мы удалили при миграции на веб-сервер (`860a6f9`), но
  per-module код инструментов ещё лежит в git: `src/modules/team/mcp/{member,contact}.py`
  + `src/apps/mcp_team/server.py` (instructions, обход установки версии). Это prior art для
  воскрешения; рабочая копия выгружена в `temp/semaphore-old-mcp` (ветка `old-mcp` =
  `860a6f9^`). Старые файлы используют **bundled** `mcp.server.fastmcp.FastMCP` и держат в
  каждом `register(mcp)` вложенные `@mcp.tool()` — CRUD уже полный.
- Решения, принятые в обсуждении (этот чат):
  - **Имена: ось `McpClient` / `McpServer`.** `llm_providers` — это MCP-**клиент** (мы
    потребляем чужие серверы: `McpClient`/`McpManager`, таблица `llm_providers_mcp_servers`,
    routes `/internal/.../mcp/servers/{code}`). Этот план — MCP-**сервер** (мы отдаём свои).
    Всё новое называем `McpServer*` / `mcp_server*`; пересечений нет, т.к. имена
    квалифицированы пакетом (`src.core.mcp` vs `llm_providers.tools.mcp`) и ролью.
  - **Регистрация: словарь `mcp_servers: dict[str, McpServerBuilder]`** на `Module` (зеркало
    декларативного `Module.guards`). Ключ `code` = URL-сегмент (`/mcp/<code>`); значение —
    **функция-конструктор** (всегда именуется `mcp_server`), а не экземпляр. Функция-значение
    решает ленивость: определение словаря НЕ исполняет конструктор → `fastmcp` не
    импортируется в момент `build_modules()` → воркер чист. Модуль может декларировать
    **несколько** серверов (несколько ключей). Пустой словарь = не-MCP-модуль.
  - **Форк, а не bundled.** Bundled стоит ~0 МБ (серверная часть лежит внутри `mcp`, уже
    импортируемого клиентом), но без композиции/middleware. Форк стоит **+13 МБ** (замерено,
    поверх `mcp`, от которого он зависит — `mcp` убрать нельзя) и даёт **композицию серверов
    + 11 middleware-хуков (per-tool аудит/гейтинг) + in-memory тестовый Client + трансформацию
    инструментов**. Для растущего `/mcp` с CRUD-наружу + аудитом — оправдано. См. исследование
    [[fastmcp]] + файл расхождений standalone.
  - **Монтаж по путям.** Одна зона ядра `/mcp`, под ней N **отдельно смонтированных**
    FastMCP-приложений по разным URL (`/mcp/team`, …) — НЕ серверная композиция форка (она
    даёт один эндпоинт с namespaced-инструментами). Пользователю нужны разные эндпоинты/обработчики.
  - **Auth через TokenVerifier, не FastAPI guard.** Смонтированное ASGI-подприложение
    обходит FastAPI `dependencies=[...]` (token-Depends из `make_zone_guard` не выполняется
    через границу монтажа). Поэтому текущий `core/router/mcp.py` (`build_mcp_zone` APIRouter +
    `MCP_DEFAULT_GUARDS=["token"]`) НЕ защищает смонтированные FastMCP-приложения и должен
    быть заменён сборкой на монтаже. Auth живёт в `McpServerTokenVerifier`, который зовёт
    инъецированный `resolve_token(token, "mcp")` (проверка, что scope токена = `mcp`).
- Проверена поверхность форка 3.4.1 (интроспекция): `FastMCP.http_app(path, middleware,
  json_response, stateless_http, transport='http'|'streamable-http'|'sse')` →
  `StarletteWithLifespan` (открывает `.lifespan` → решает подводный камень mount-lifespan);
  базовые классы auth `TokenVerifier`/`AuthProvider`/`RemoteAuthProvider`
  (`TokenVerifier.verify_token` — точка-хук); серверный middleware через `add_middleware`
  (`on_call_tool`, `on_request`, …).
- Координируется с двумя соседними работами:
  - **Разрешение токена** = план `2026-06-06-mcp-user-tokens.md` (журнал решений: задача
    `2026-06-05-mcp-user-tokens.md`). **ГОТОВО ЦЕЛИКОМ** — таблица (`cu05_user_tokens`),
    `service/token.py`, routes (`/me/tokens` POST/GET/DELETE с guard `token_owner` +
    `/users/{id}/tokens` GET/DELETE admin), фронтенд (`TokensCard`/`CreateTokenDialog`) и
    тесты (`test_token.py`/`test_token_api.py`) уже выгружены. Ключевое для нас:
    core_users `service/token.resolve_token(full_token, scope) -> User | None` существует
    (селектор `public_id` → строка → `compare_token_hash` → совпадение scope + срок →
    `is_active` → сдвиг `last_used_at`), возвращает принципала `dto/principal.User`, и сейчас
    у него **ноль вызывающих** — этот план его первый и единственный потребитель.
    Единственное, что этот план добавляет на токен-стороне, — `McpServerTokenVerifier`,
    зовущий `resolve_token(token, "mcp")`. Заглушка не нужна. (`scope` — это auth-scope
    токена, `TOKEN_SCOPES=('mcp','api')`, `DEFAULT_SCOPE='mcp'`, намеренно отличается от
    *зоны* роутера `/mcp`; токен со scope `mcp`, предъявленный в другом месте, — бесплатный
    reject. Guard `token_owner` защищает *управляющие* routes токенов — это НЕ MCP
    server-auth, которым занимается этот план.)
  - **Ядро остаётся модуль-агностичным (жёсткий инвариант).** `src/core/` никогда не
    импортирует `src/modules/*`: реальные `auth`/`ability` *вливаются* `core_users` через
    реестр `Module.guards` (`build_guard_registry`), а `core/api/__init__.py` пишет это прямым
    текстом («Ядро НЕ знает о пользователях»). Поэтому верификатор НЕ имеет права делать
    `import core_users.resolve_token` из `core/mcp`. Резолвер **инъецируется**, зеркаля
    `guards`: см. Подход + шаги 2/4/5.
  - **nginx**-проксирование стрима = `2026-06-05-nginx-mcp-streaming` (специфицировано; один
    `location /mcp/` покрывает все подприложения).
- Замечание о вытеснении: зона `/mcp` сегодня — это СТАРАЯ APIRouter-обвязка
  (`core/router/mcp.py::build_mcp_zone` + `MCP_DEFAULT_GUARDS=["token"]`, монтируется
  `core/router/mounting.py::mount_router_zones`, когда модуль даёт `mcp_router`). Этот план
  ЗАМЕНЯЕТ её смонтированными FastMCP-приложениями — поэтому ссылки токен-плана на
  `mcp_router` + дефолтный зон-guard `token` для MCP-серверов неактуальны (auth — это
  `McpServerTokenVerifier`→`resolve_token`, которого монтаж реально достигает; FastAPI
  Depends — нет).

## Объём

**В объёме:**
- Добавить зависимость `fastmcp`, лениво + только в backend (без удара по RSS воркера).
- Новый контракт ядра `Module.mcp_servers` (декларативный словарь `code → mcp_server`) +
  сборка на монтаже в `create_app`, заменяющая APIRouter-зону `/mcp`. Поддержка нескольких
  серверов на модуль.
- Auth-адаптер `McpServerTokenVerifier` (модуль-агностичный, в `core/mcp`), потребляющий
  **инъецированный** резолвер — `core_users` поставляет `resolve_token(token, "mcp")` через
  новый декларативный `Module.mcp_token_resolver` (зеркало `Module.guards`; держит ядро
  снаружи `core_users`) — + per-tool audit-middleware + `transport_security` (allowed_hosts
  против DNS-rebinding).
- MCP-сервер `team` (полный CRUD: members + contacts) как эталонная реализация.
- Тесты на in-memory `Client` + тест boot/lifespan.

**Вне объёма:**
- Таблица токенов / хеширование / TTL **и сам резолвер `resolve_token`** — план
  `2026-06-06-mcp-user-tokens.md` (**уже готов**). Этот план его только вызывает.
- Конфиг nginx — `2026-06-05-nginx-mcp-streaming`.
- MCP-серверы для других модулей (conversations, …) — по паттерну team, позже.
- Миграция потребительской стороны (`tools/mcp/client.py` `McpClient`) на `fastmcp.Client` —
  выигрыша по памяти нет (`mcp` остаётся), отдельная зачистка, если вообще понадобится.
- Фронтенд (UI самообслуживания токенов **уже выгружен** в токен-задаче —
  `TokensCard`/`CreateTokenDialog`; этот план фронтенд не трогает).

## Подход

Модуль декларирует свои MCP-серверы словарём **`mcp_servers: dict[str, McpServerBuilder]`**
(зеркало `Module.guards`): ключ — `code` (= URL-сегмент `/mcp/<code>`), значение — функция
`mcp_server(ctx) -> FastMCP` (всегда так названа). Значение — **функция, а не экземпляр** —
поэтому определение словаря не импортирует `fastmcp`, и воркер чист (метод-хук ради
ленивости больше не нужен — её решает сама природа значения-функции). Модуль может
декларировать несколько серверов.

`create_app` только в ветке `server_enabled` зовёт `mount_mcp_servers(app, modules, config)`:
он один раз строит `McpServerContext` (общий `McpServerTokenVerifier` + `McpServerAuditMiddleware`
+ `transport_security`), затем на каждый `(code, mcp_server)` всех модулей вызывает
`mcp_server(ctx)`, монтирует `mcp.http_app(transport="streamable-http")` под `/mcp/<code>` и
**композирует возвращённые `.lifespan`-ы** в lifespan приложения через `AsyncExitStack` (там
живёт инициализация session manager форка). Дубль `code` между модулями → `RuntimeError` на
boot (громкий отказ, не тихий перезатёр).

Auth — это форковский `TokenVerifier.verify_token(token)` → **инъецированный** резолвер
(`resolve_token(token, scope="mcp")` → `User | None`, поставленный core_users). Верификатор
(`McpServerTokenVerifier`, агностичный) проверяет, что scope токена = `mcp`, и мапит
возвращённого принципала в MCP `AccessToken` (`client_id=str(user.id)`, `scopes=[user.group]`).
Резолвер инъецируется — НЕ импортируется ядром — ровно так же, как `core_users` вливает свои
guard'ы `auth`/`ability` в реестр ядра; `mount_mcp_servers` собирает его из
`Module.mcp_token_resolver`. Bearer-проверка выполняется внутри смонтированного приложения —
единственное место, переживающее границу монтажа.

**Отвергнутая альтернатива:** оставить APIRouter-зону `core/router/mcp.py` + `token`-Depends
и писать MCP поверх FastAPI-роутов руками — отвергнуто, потому что Streamable HTTP требует
ASGI-уровневого контроля сессии/стрима; пришлось бы переписывать протокол и потерять SDK
целиком.

**Отвергнутая альтернатива:** форковский `mcp.mount()` server-composition в один эндпоинт
`/mcp` — отвергнуто, потому что он namespace-ит инструменты под одним соединением; нам нужны
разные эндпоинты `/mcp/<code>` с независимыми обработчиками и instructions.

## Схема файлов

MCP-**основа** (ядро, модуль-агностичная) — самое важное: это переиспользуемая
«платформенная» половина. Модуль подключается **одним словарём** (`mcp_servers`) и получает
монтаж + auth + аудит + lifespan + transport-security даром. `team` — лишь первый потребитель
этой основы.

### Основа ядра (переиспользуемая — модуль-агностичная)

MCP-инструментарий живёт в **одном новом подпакете ядра `src/core/mcp/`** — он изолирует
импорт `fastmcp` в одно backend-only место (держит +13 МБ снаружи воркера И снаружи
`core_users`) и даёт модулям одну точку импорта (`from src.core.mcp import …`). Зон-монтажный
клей остаётся в `core/router/mcp.py` рядом с другими зонами. **НЕ модуль `core_mcp`:** основа
И ЕСТЬ сборщик — она правит контракт `Module` и монтирует приложения других модулей в
`create_app`; зарегистрированный модуль так не может. (`core_mcp` станет модулём, только если
позже захотим управляющую/админскую поверхность — список смонтированных серверов, рантайм-
переключение. Вне объёма.)

```
src/core/
├── module.py                  # MOD  + mcp_servers: ClassVar[dict[str, McpServerBuilder]] = {}  (code → mcp_server)
│                              #      + classvar mcp_token_resolver (зеркало `guards`; ставит core_users)
│                              #      (ЗАМЕНЯЕТ mcp_router / mcp_router_prefix)
├── config.py                  # MOD  + mcp_allowed_hosts  (питает transport_security)
├── app_factory.py             # MOD  композиция lifespan-ов смонтированных серверов в lifespan create_app (AsyncExitStack)
├── mcp/                       # НОВЫЙ ПОДПАКЕТ — MCP-server-инструментарий (единственная граница импорта `fastmcp`)
│   ├── __init__.py            #      фасад: McpServerContext, McpServerBuilder, make_mcp_server
│   ├── context.py             #      McpServerContext (auth / audit / transport_security)
│   │                          #      + McpServerBuilder = Callable[[McpServerContext], FastMCP]
│   ├── auth.py                #      McpServerTokenVerifier(TokenVerifier) — АГНОСТИЧНЫЙ: оборачивает ИНЪЕЦИРОВАННЫЙ
│   │                          #      резолвер `(token,scope)->principal|None`; verify_token → resolve(token,"mcp"); БЕЗ импорта core_users
│   ├── audit.py               #      McpServerAuditMiddleware (форковский серверный middleware on_call_tool → log mcp/audit)
│   └── factory.py             #      make_mcp_server(code, instructions, ctx) — одна сборка FastMCP под ctx
└── router/
    ├── mcp.py                 # ПЕРЕПИСАТЬ  убрать build_mcp_zone / MCP_DEFAULT_GUARDS;
    │                          #      ЗОН-клей: mount_mcp_servers(app,modules,config)->list[Lifespan] (+ MCP_PREFIX), зовёт core/mcp/
    └── mounting.py            # MOD  mount_router_zones: ветка mcp build_mcp_zone→mount_mcp_servers; пробросить lifespan-ы наверх
pyproject.toml                 # MOD  + fastmcp>=3.4,<4 ; поднять mcp>=1.24      (uv.lock MOD)
```

### Контракт основы (вся архитектура в 5 символах)

```python
# core — модуль-агностичная, «платформенная» половина MCP-сервера
McpServerBuilder = Callable[["McpServerContext"], "FastMCP"]   # конструктор; всегда именуется mcp_server

class McpServerContext:                     # общая обвязка, отдаваемая конструктору каждого модуля
    auth: TokenVerifier                     #   = McpServerTokenVerifier (один экземпляр, все серверы)
    audit: Middleware                       #   = McpServerAuditMiddleware
    transport_security: TransportSecuritySettings   # allowed_hosts (DNS-rebinding)

class Module:                               # базовый контракт, наследуемый каждым модулем
    mcp_servers: ClassVar[dict[str, "McpServerBuilder"]] = {}   # code → mcp_server; пусто = не-MCP-модуль
    #   значение — ФУНКЦИЯ (ленивость), не экземпляр; модуль может дать несколько серверов

class McpServerTokenVerifier(TokenVerifier):  # АГНОСТИЧНЫЙ — без импорта core_users; резолвер инъецирован
    def __init__(self, resolve):              #   resolve: (token, scope) -> principal | None  (core_users.resolve_token)
        ...
    async def verify_token(self, token) -> "AccessToken | None":  # → resolve(token,"mcp") (scope=mcp); principal→AccessToken(scopes=[group])
        ...

# core_users поставляет резолвер декларативно (зеркало `Module.guards`):
class CoreUsersModule(Module):
    mcp_token_resolver = staticmethod(resolve_token)   # ядро собирает его в mount_mcp_servers — никогда не импортирует

def make_mcp_server(code, instructions, ctx) -> "FastMCP":  # FastMCP(name=code, auth=ctx.auth, transport_security=…) + add_middleware(ctx.audit)
    ...

def mount_mcp_servers(app, modules, config) -> list[Lifespan]: ...  # строит ctx; per (code, mcp_server): дубль→RuntimeError, монтирует /mcp/<code>

# Прописка: McpServerContext / McpServerBuilder / auth / audit / make_mcp_server → src/core/mcp/   ·
#           classvar Module.mcp_servers + mcp_token_resolver → core/module.py   ·
#           mount_mcp_servers (собирает резолвер, строит верификатор) → core/router/mcp.py
```

### team — эталонный потребитель (per-module паттерн)

Воскрешение из `temp/semaphore-old-mcp` (= `860a6f9^`): `mv` файлы, правим только изменённое.
Старый `__init__.py` был пустой (сборку держал `apps/mcp_team/server.py`) — теперь в нём
живёт конструктор `mcp_server`. Старые `member.py`/`contact.py` держат `register(mcp)` как
есть; меняем только импорт `FastMCP` (bundled → форк, под `TYPE_CHECKING`) и декораторы под
форк 3.x.

```
src/modules/team/
├── module.py                  # MOD  + mcp_servers = {"team": mcp_server}   (импорт mcp_server из team.mcp)
└── mcp/                       # mv из 860a6f9^:src/modules/team/mcp/* (top-level БЕЗ runtime-импорта fastmcp)
    ├── __init__.py            #      def mcp_server(ctx): make_mcp_server("team", INSTRUCTIONS, ctx)
    │                          #      + member.register(mcp) + contact.register(mcp)   (был пустой → наполняем)
    ├── member.py              #      register(mcp): member_list/get/create/update/delete (→ team crud, полный CRUD)
    └── contact.py             #      register(mcp): contact_create/update/delete        (→ team crud, полный CRUD)
```

### Тесты / env / docs

```
tests/modules/team/test_mcp_server.py  # НОВЫЙ  in-memory форк-Client(mcp_server(ctx)): CRUD member+contact, dup-contact, not-found, query-match
tests/core/test_mcp_server_auth.py     # НОВЫЙ  McpServerTokenVerifier: scope=mcp → принципал→AccessToken(scopes=[group]); None при resolve→None / чужом scope
tests/core/test_app_factory.py         # MOD  boot монтирует /mcp/team; lifespan композируется; дубль code→RuntimeError; `fastmcp` НЕ в sys.modules в worker-режиме
.env.example.* (+ реальный .env)       # MOD  MCP_ALLOWED_HOSTS
dev/docs/ENV.md                        # MOD  задокументировать MCP_ALLOWED_HOSTS
AGENTS/memory/*.md                     # MOD  зафиксировать поверхность серверов /mcp + контракт Module.mcp_servers + словарь client/server
```

### Поток

```
build-time (только backend — SERVER_ENABLED):
  create_app(modules) ─► mount_router_zones(...) ─► mount_mcp_servers(app, modules, config)
      ctx = McpServerContext(McpServerTokenVerifier(resolver), McpServerAuditMiddleware, transport_security)
      seen = set()
      for m in modules:
          for code, mcp_server in m.mcp_servers.items():
              if code in seen: raise RuntimeError(f"duplicate mcp server code: {code}")
              mcp = mcp_server(ctx)                  # лениво, backend-only (воркер не зовёт → нет +13 МБ)
              sub = mcp.http_app("streamable-http", stateless_http=True)
              app.mount(f"/mcp/{code}", sub);  собрать sub.lifespan
      └─ lifespan-ы всплывают в create_app, композируются через AsyncExitStack (инициализация session-manager)

request-time:
  client ─► nginx(location /mcp/, buffering off) ─► FastAPI mount /mcp/team ─► FastMCP(team)
      ├─ verify_token(bearer) → resolve_token(token,"mcp") → User | 401
      └─ on_call_tool (аудит) → tool(member_create) → team crud → DB
```

## Шаги

1. **Зависимость + дисциплина импорта** — добавить `fastmcp>=3.4,<4` в основные деп-ы;
   поднять нижнюю границу `mcp` до `>=1.24` (требование форка). `fastmcp` должен
   импортироваться ТОЛЬКО внутри подпакетов `mcp/` модулей (в телах конструкторов / под
   `TYPE_CHECKING`) и в сборщике монтажа ядра — никогда на верхнем уровне исполняемого кода,
   который тянет `build_modules()` (держит его снаружи воркера). Файлы: `pyproject.toml`,
   `uv.lock`.
2. **Auth-адаптер** — `McpServerTokenVerifier(TokenVerifier)`, **модуль-агностичный**: ctor
   принимает инъецированный `resolve: Callable[[str, str], Awaitable[principal | None]]`;
   `verify_token` делает `user = await resolve(token, "mcp")` (проверка scope=mcp) → на
   принципале возвращает `AccessToken(client_id=str(user.id), scopes=[user.group])`, иначе
   `None`. БЕЗ импорта `core_users` (принципал — duck-typed `.id`/`.group`, либо
   `Protocol`/TYPE_CHECKING-тип) — держит инвариант ядра. Реальный резолвер — core_users
   `service/token.resolve_token` (уже приземлился — без заглушки), инъецируется в
   `mount_mcp_servers` (шаг 5). Этот файл — **начало границы импорта `fastmcp` в `core/mcp/`**.
   Файлы: `src/core/mcp/auth.py` (новый).
3. **Audit-middleware** — форковский серверный middleware с `on_call_tool`, логирующий
   `principal · tool · сводка-аргументов · ok/err · ms` в канал логгера `mcp/audit`.
   Файлы: `src/core/mcp/audit.py` (новый).
4. **Контракт Module** — заменить `Module.mcp_router`/`mcp_router_prefix` на
   `mcp_servers: ClassVar[dict[str, McpServerBuilder]] = {}` (`code → mcp_server`; импорт
   `McpServerBuilder` только под TYPE_CHECKING). Также добавить
   `mcp_token_resolver: ClassVar[TokenResolver | None] = None` (зеркало `guards` —
   декларативный шов, которым ядро получает резолвер БЕЗ импорта модуля); `core_users` ставит
   его в `staticmethod(resolve_token)`. Файлы: `src/core/module.py`,
   `src/modules/core_users/module.py`.
5. **Инструментарий + сборщик монтажа** — `core/mcp/`: `context.py` (`McpServerContext` +
   `McpServerBuilder`), `factory.py` (`make_mcp_server(code, instructions, ctx)`), фасад
   `__init__.py`. Затем переписать `core/router/mcp.py`: убрать `build_mcp_zone`/
   `MCP_DEFAULT_GUARDS`; добавить `mount_mcp_servers(app, modules, config) -> list[lifespan]`,
   который строит контекст один раз: **собрать единственный `mcp_token_resolver` с модулей**
   (как `build_guard_registry`; поставляет core_users) → `McpServerTokenVerifier(resolver)` +
   `McpServerAuditMiddleware` + `transport_security` из `config.mcp_allowed_hosts`. Затем по
   всем `(code, mcp_server)` модулей: дубль `code` → `RuntimeError`;
   `app.mount(f"{MCP_PREFIX}/{code}", mcp_server(ctx).http_app(transport="streamable-http",
   stateless_http=True))`, собирая каждый `.lifespan`. Файлы:
   `src/core/mcp/{__init__,context,factory}.py`, `src/core/router/mcp.py`.
6. **Зон-обвязка + lifespan** — в `core/router/mounting.py::mount_router_zones` заменить
   ветку mcp `build_mcp_zone`/`_attach_zone` на `mount_mcp_servers`; пробросить возвращённые
   lifespan-ы наверх в `create_app` и композировать их в CM `lifespan` через `AsyncExitStack`
   (там живёт инициализация session-manager форка). Файлы: `src/core/router/mounting.py`,
   `src/core/app_factory.py`.
7. **MCP-сервер team** — `mv` `src/modules/team/mcp/{__init__,member,contact}.py` из
   `temp/semaphore-old-mcp` (= `860a6f9^`); `member.py`/`contact.py` держат `register(mcp)`
   как есть, меняем только импорт `FastMCP` (bundled `mcp.server.fastmcp` → форк `fastmcp`,
   под TYPE_CHECKING) и декораторы под форк 3.x. В `__init__.py` пишем
   `def mcp_server(ctx): mcp = make_mcp_server("team", <instructions из старого
   mcp_team/server.py>, ctx); member.register(mcp); contact.register(mcp); return mcp`.
   `TeamModule.mcp_servers = {"team": mcp_server}`. Полный CRUD. Файлы:
   `src/modules/team/mcp/*`, `src/modules/team/module.py`.
8. **Конфиг** — `transport_security` allowed hosts из env (напр. `MCP_ALLOWED_HOSTS`),
   дефолт localhost в dev. Файлы: `src/core/config.py` (или core_users/конфиг модуля),
   `.env.example.*`.

## Тесты

- **Юнит (in-memory `Client`)** — `tests/modules/team/test_mcp_server.py`: гоняем
  `mcp_server(ctx)` (из `team.mcp`) через форк-`Client(mcp)` (без сокетов): list/get/create/
  update/delete member + contact, ошибка дубля contact, ошибки not-found, совпадение по
  query на значении contact. Покрывает поведение инструментов end-to-end по реальному
  MCP-протоколу.
- **Юнит (auth)** — `McpServerTokenVerifier.verify_token` мапит resolved-принципала (scope=mcp)
  → `AccessToken(scopes=[group])` и возвращает `None`, когда `resolve_token` вернул `None`
  (резолвер замокан; в т.ч. кейс чужого scope). Покрывает контракт адаптера.
- **Интеграция (boot/mount/lifespan)** — `tests/core/test_app_factory.py` (или новый):
  тестовое приложение с `TeamModule` бутится, `/mcp/team` смонтирован, дубль `code` между
  модулями → `RuntimeError`, композированный lifespan входит (session manager
  инициализирован), хендшейк `initialize` через ASGI/in-memory-клиент успешен. Покрывает
  подводный камень композиции mount-lifespan + коллизию `code`.
- **Дисциплина импорта** — проверить, что импорт `build_modules()` / приложения в worker-
  режиме НЕ импортирует `fastmcp` (напр. `sys.modules` после worker-style boot). Покрывает
  гарантию backend-only RSS.

## Валидация

- Замерить RSS: backend (`SERVER_ENABLED=true`) показывает ~+13 МБ против до-изменения;
  воркер (`SERVER_ENABLED=false`) показывает **0** дельты. Записать цифры (привязка к
  `2026-06-05-memory-footprint-reduction`).
- `curl -N http://127.0.0.1:<port>/mcp/team` (после nginx: `https://host/mcp/team`) —
  Streamable-HTTP эндпоинт отвечает и стримит инкрементально (не всё разом).
- Подключить реального MCP-клиента (Claude Desktop / форк-`Client`) к `/mcp/team`:
  `tools/list` возвращает инструменты members/contacts; `member_create` + `member_list`
  отрабатывают round-trip.
- Битый/отсутствующий bearer → отклонён верификатором (401), до инструментов не доходит.

## Риски / открытые вопросы

- **Открыто:** `stateless_http=True` (выбранный дефолт — без in-memory session affinity,
  согласуется с заметкой по session-affinity в nginx) vs stateful session manager.
  Подтвердить перед шагом 6; stateless проще и безопасен по масштабу для CRUD-инструментов.
- **Решено:** принципал = core_users `dto/principal.User`; MCP scopes = `[user.group]`.
  Верификатор потребляет `resolve_token(token, "mcp")` — без отдельного типа `McpPrincipal`.
- **Решено (имена):** ось `McpClient` (`llm_providers`, потребляем) / `McpServer` (этот
  план, отдаём); всё новое — `McpServer*`/`mcp_server*`. Конструктор всегда `mcp_server`,
  словарь `Module.mcp_servers`, ключ `code` = URL-сегмент.
- **Решено (было sequencing):** токен-задача **готова целиком** (таблица + сервис + routes +
  guard `token_owner` + фронтенд + тесты); `resolve_token` существует с нулём вызывающих;
  без заглушки, без параллельной интеграции. Этот план — его первый потребитель.
- **Решено (архитектура):** держим `src/core/` модуль-агностичным. Верификатор
  `McpServerTokenVerifier` агностичен + принимает инъецированный резолвер; `core_users`
  поставляет `resolve_token` через новый декларативный `Module.mcp_token_resolver` (зеркало
  `Module.guards`), который собирает `mount_mcp_servers`. Ядро никогда не импортирует
  `core_users`. (Отвергнутая альт.: дать сборщику импортировать `resolve_token` напрямую —
  дёшево, но первая трещина в инварианте.)
- **Решено (ленивость):** значение `mcp_servers` — функция-конструктор, а не экземпляр →
  определение словаря не импортирует `fastmcp`. Дисциплина: файл с конструктором
  (`team/mcp/__init__.py`) и tool-файлы не импортируют `fastmcp` на верхнем уровне (только в
  телах / под `TYPE_CHECKING`), т.к. их тянет `build_modules()` и в воркере.
- **Риск:** утечка верхнеуровневого импорта `fastmcp` в воркер → +13 МБ везде.
  Митигация: значения-функции + дисциплина импорта + тест дисциплины импорта.
- **Риск:** форк 3.x быстро движется / не API-совместим с bundled. Митигация: строгий пин
  + `uv.lock`; всё использование форка изолировано в подпакетах `mcp/` + сборщике.
- **Риск:** mount-lifespan не композирован → session manager не инициализирован → 500.
  Митигация: явный `AsyncExitStack` над каждым `http_app().lifespan`; boot-тест проверяет.
- **Заметка:** удаление `Module.mcp_router` безопасно — его пока ни один модуль не реализует
  (ссылается только каркас ядра).

## Ссылки

- Соседний план: `AGENTS/plans/2026-06-06-mcp-user-tokens.md` (**готов** — построил
  `resolve_token`, который этот план потребляет)
- Связанные задачи: `AGENTS/tasks/2026-06-05-nginx-mcp-streaming.md`,
  `AGENTS/tasks/2026-06-05-mcp-user-tokens.md`
- Исследование: `AGENTS/research/fastmcp/INDEX.md`,
  `AGENTS/research/nginx-mcp-streaming/INDEX.md`
- Prior art (git): `860a6f9^:src/modules/team/mcp/*`, `860a6f9^:src/apps/mcp_team/server.py`;
  рабочая копия — `temp/semaphore-old-mcp` (ветка `old-mcp`)
- Память: `project_core_llm_module`, `project_llm_providers_mcp_servers`
- Текущий каркас ядра: `src/core/router/mcp.py`, `src/core/router/mounting.py`,
  `src/core/module.py`, `src/core/app_factory.py`
```
