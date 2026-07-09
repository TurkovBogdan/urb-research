# Как хранится сессия на фронте и что такое httpOnly-cookie

Урок про то, как у нас устроена аутентификация: где «живёт» сессия, почему токен
**не** хранится в JavaScript, и как браузер с бэкендом договариваются «кто ты».
Разбор на реальном коде (`web/src/`, `src/modules/core_users/`).

---

## 1. Главная мысль: сессия НЕ хранится на фронте

Это первое, что нужно перевернуть в голове. Интуиция подсказывает: «логинюсь →
получаю токен → сохраняю его в `localStorage` → прикладываю к каждому запросу в
заголовке `Authorization`». Так делают многие, и это **дырявый** подход.

У нас по-другому. Сформулируем сразу, а ниже распакуем по частям:

- **Фронт не хранит токен вообще.** Ни в `localStorage`, ни в `sessionStorage`, ни в
  переменной JS. Открой DevTools → Application → Local Storage — токена там нет.
- **Токен живёт в cookie**, которую выставляет бэкенд и которую **JavaScript не может
  прочитать** (флаг `httpOnly`).
- **Состояние сессии хранится на сервере** — в таблице `core_users_sessions`. Cookie
  — это просто «ключ от ячейки», а сама ячейка (кто пользователь, когда протухнет) на
  бэкенде.

То, что фронт держит в памяти (Pinia-store `auth`) — это **не сессия**, а лишь её
проекция: «кто я и что мне можно». При перезагрузке страницы оно теряется и
восстанавливается заново запросом `/me`. Сессия же переживает перезагрузку, потому что
живёт в cookie + БД.

---

## 2. Что такое cookie и при чём тут «httpOnly»

**Cookie** — маленький кусочек данных (`имя=значение`), который сервер просит браузер
сохранить, а браузер потом **сам, автоматически** прикладывает к каждому запросу на
этот домен. Программисту на фронте делать для этого ничего не надо — это механика
самого браузера.

Сервер заводит cookie заголовком ответа:

```
Set-Cookie: sid=AbCd...xyz; HttpOnly; Secure; SameSite=Strict; Max-Age=14400; Path=/
```

Дальше браузер на каждый запрос к нашему домену автоматически добавляет:

```
Cookie: sid=AbCd...xyz
```

Те слова после `sid=...` — это **флаги-атрибуты**, они и делают cookie безопасной. Разберём
каждый на нашем коде (`src/modules/core_users/api.py`):

```python
def _set_session_cookie(response: Response, token: str) -> None:
    cfg = get_config()
    response.set_cookie(
        key=cfg.session_cookie_name,        # "sid"
        value=token,                        # сырой токен (32 байта urlsafe)
        max_age=cfg.session_lifetime,       # 14400 сек = 4 часа
        httponly=True,
        secure=cfg.session_cookie_secure,   # dev=False, прод за TLS=True
        samesite=cfg.session_cookie_samesite,  # "strict"
        path="/",
    )
```

### `HttpOnly` — главный флаг урока

`httpOnly=True` означает: **cookie доступна только HTTP-слою (браузеру при отправке
запросов), но НЕ доступна JavaScript.** Код `document.cookie` её просто не увидит —
вернёт пустоту на месте `sid`.

Зачем? Это защита от **XSS** (cross-site scripting — когда злоумышленник как-то
впихнул свой `<script>` на твою страницу). Если бы токен лежал в `localStorage` или в
обычной cookie, вражеский скрипт прочитал бы его одной строкой и угнал сессию. А
httpOnly-cookie он украсть не может — браузер физически не отдаёт её в JS. Скрипт может
заставить браузер сделать запрос (cookie уедет автоматически), но **вынести токен
наружу** — нет.

Вот плата за это (и почему фронт-код «не знает» про токен) — комментарий из нашего
HTTP-клиента (`web/src/api/client/internal.ts`):

```
//  - The session is an httpOnly, SameSite=strict cookie: no token in JS (XSS can't
//    read it), CSRF is covered by SameSite — so we send no Authorization header.
```

### Остальные флаги

- **`Secure`** — cookie уезжает только по HTTPS, не по голому HTTP. В проде `True` (мы
  за TLS), в dev `False` (локалка по http, иначе cookie бы не выставилась).
- **`SameSite=Strict`** — браузер прикладывает cookie **только** когда запрос идёт с
  нашего же сайта. Если пользователь на `evil.com` и тот шлёт запрос на наш бэкенд —
  cookie **не** уедет. Это защита от **CSRF** (когда чужой сайт исподтишка дёргает наш
  API от имени залогиненного юзера). Именно поэтому нам не нужны CSRF-токены — за нас
  работает `SameSite`.
- **`Max-Age=14400`** — сколько секунд браузер хранит cookie (4 часа). После — браузер
  сам её выбросит.
- **`Path=/`** — cookie действует на все пути сайта.

---

## 3. Что лежит в cookie — и почему это НЕ опасно даже если утечёт

В cookie лежит **сырой случайный токен** — 32 байта из криптографического генератора
(`src/modules/core_users/security.py`):

```python
def new_session_token() -> str:
    """Сырой токен сессии (в cookie). В БД класть ЕГО ХЕШ, не сам токен."""
    return secrets.token_urlsafe(32)
```

Это **не** JWT, не зашифрованные данные пользователя — просто непредсказуемая строка-
«пропуск». Сам по себе он ничего не значит; смысл ему придаёт запись в БД.

Ключевой приём безопасности: **в базе хранится не токен, а его SHA-256-хеш.**

```python
def hash_session_token(token: str) -> str:
    """Стабильный sha256-хеш токена сессии для хранения/поиска в БД."""
    return hashlib.sha256(token.encode()).hexdigest()
```

Зачем хешировать? Если злоумышленник как-то получит дамп таблицы `core_users_sessions`,
он увидит только хеши — а из хеша обратно токен не восстановить. Подставить хеш в
cookie бесполезно: бэкенд хеширует то, что пришло в cookie, и сравнивает. Это та же
логика, что и с паролями — **в БД никогда не лежит то, что предъявляет клиент**.

Итого схема таблицы `core_users_sessions` (`models.py`):

| колонка        | смысл                                              |
|----------------|----------------------------------------------------|
| `id`           | PK                                                 |
| `user_id`      | FK → `core_users.id`, `ON DELETE CASCADE`          |
| `token_hash`   | SHA-256 от cookie-токена (`unique`)                |
| `created_at`   | когда сессия создана                               |
| `last_used_at` | последнее использование — для idle-таймаута        |
| `expires_at`   | абсолютный потолок жизни сессии                    |

---

## 4. Полный путь: что происходит при логине

```
LoginView.vue                 auth store (Pinia)          бэкенд core_users
─────────────                 ──────────────────          ─────────────────
submit(email, pwd) ─────────► auth.login() ─────────────► POST /core-users/auth/login
                                                            │
                                                            │ verify Argon2id
                                                            │ create session row (token_hash)
                                                            │ Set-Cookie: sid=<токен>; HttpOnly...
                                                            ▼
                              _apply(UserView) ◄───────── вернул UserView { email, group, abilities }
                              ability.update(rules)
```

Шаг за шагом:

1. **Форма** (`web/src/views/auth/LoginView.vue`) зовёт `auth.login(email, password)`.
2. **Стор** (`web/src/stores/auth.ts`) шлёт `POST /core-users/auth/login`.
3. **Бэкенд** (`api.py::login`):
   - проверяет пароль через Argon2id (`service/auth.py`, см. ниже);
   - создаёт строку сессии в БД (`service/session.py::create`) — генерит сырой токен,
     кладёт в БД его **хеш** и `expires_at = now + 4 ч`;
   - выставляет httpOnly-cookie `sid` с **сырым** токеном;
   - возвращает `UserView` с полями `email`, `group` и `abilities` (CASL-правила).
4. **Стор** кладёт `UserView` в `user` и перестраивает CASL-`ability` из `abilities`:

```typescript
function _apply(next: UserView | null): void {
  user.value = next
  ability.update(next?.abilities ?? [])   // права для UI ($can в шаблонах)
}
```

Обрати внимание: **токен из ответа в JS не приходит и нигде не сохраняется.** Бэкенд
положил его в cookie заголовком `Set-Cookie`, дальше им рулит браузер. Стор хранит
только «личность и права» — для отрисовки UI.

---

## 5. Что происходит на каждом следующем запросе

Здесь и видно всю прелесть подхода — **фронт не делает ничего**.

```typescript
// web/src/api/client/internal.ts
const CREDENTIALS: RequestCredentials = ORIGIN ? 'include' : 'same-origin'
// ...
const init: RequestInit = { method, credentials: CREDENTIALS, headers, signal: opts.signal }
res = await fetch(buildUrl(path, opts.query), init)
```

Единственное, что нужно — `credentials: 'same-origin'` в `fetch`. Это говорит браузеру
«прикладывай cookie к запросу на свой origin». Никакого `Authorization`, никакого
ручного чтения токена. Браузер сам добавит `Cookie: sid=...`.

На бэкенде каждый защищённый маршрут проходит через guard (`guards.py::guard_auth`):

```python
async def guard_auth(request: Request) -> None:
    """Вид auth: cookie → живая сессия → принципал в request.state.user."""
    raw = request.cookies.get(get_config().session_cookie_name)
    user = await session_service.resolve(raw) if raw else None
    if user is None:
        raise ApiError.unauthorized("Сессия истекла")
    request.state.user = user
```

А `resolve` (`service/session.py`) — это сердце проверки:

```python
async def resolve(raw_token: str) -> User | None:
    token_hash = security.hash_session_token(raw_token)        # хешируем то, что в cookie
    row = await session_crud.get_live_by_token_hash(token_hash) # ищем живую (expires_at > now)
    if row is None:
        return None                                            # нет / протухла абсолютно

    idle = _cfg().session_idle
    if idle and row.last_used_at < utc_now() - timedelta(seconds=idle):
        await session_crud.delete_by_token_hash(token_hash)    # простой > 15 мин → гасим
        return None

    user = await user_crud.get(row.user_id)
    if user is None or not user.is_active:
        return None

    await session_crud.touch(token_hash)                       # продлеваем idle-окно
    return _principal(user)
```

Логика на пальцах: взять токен из cookie → захешировать → найти в БД живую запись →
проверить, что не протухла (ни абсолютно, ни по простою) → достать пользователя →
обновить `last_used_at`. Если что-то не так — `None`, и guard кинет 401.

Дальше роут получает пользователя через зависимость `current_user` — она просто читает
то, что guard уже положил в `request.state.user`.

---

## 6. Два уровня «протухания» сессии

Сессия мрёт по двум независимым причинам (`module_config.py`):

```python
session_lifetime: int = 14_400  # 4 ч  — абсолютный потолок
session_idle: int = 900         # 15 мин — таймаут простоя (0 = выключен)
```

1. **Абсолютный потолок (`expires_at`)** — ставится один раз при создании сессии
   (`now + 4 ч`). Проверяется прямо в SQL (`get_live_by_token_hash`: `expires_at > now()`).
   Через 4 часа сессия мертва, даже если ты ей активно пользовался. Это страховка: даже
   угнанный токен живёт максимум 4 часа.
2. **Idle-таймаут (`last_used_at`)** — каждый запрос двигает `last_used_at` вперёд
   (`touch`). Если между запросами прошло больше 15 минут — сессия гасится. Это
   автологаут «отошёл от компа».

Разница: **потолок не продлевается** активностью, **idle-окно продлевается** каждым
запросом. Поэтому даже при непрерывной работе тебя выкинет ровно через 4 часа от
логина, а при бездействии — через 15 минут от последнего клика.

---

## 7. Пароль: Argon2id (а не просто «хеш»)

Пароль пользователя в БД лежит как Argon2id-хеш (`security.py`):

```python
_pwd = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=102_400, parallelism=8),))
```

Argon2id — современный **memory-hard** алгоритм: каждое хеширование жрёт ~100 МиБ
памяти и заметное время. Это специально: перебор паролей на GPU/ASIC становится дорогим.
Поскольку хеширование CPU-bound, в `service/auth.py` его зовут через
`run_in_threadpool`, чтобы не блокировать event loop.

Есть приятная деталь — **rehash-on-login**: `verify_and_rehash` при успешном входе
проверяет, не устарели ли параметры Argon2, и если да — пересчитывает хеш и обновляет
в БД. Параметры стойкости можно поднимать со временем, и пользователи прозрачно
«переедут» на них при следующем логине.

---

## 8. Фронт: откуда он знает, залогинен ли ты (бутстрап через `/me`)

После перезагрузки страницы стор пуст (JS-память сброшена), но cookie-то на месте.
Поэтому фронт при старте делает один запрос `/me` — «кто я?» — и восстанавливает
проекцию. Это **ленивый бутстрап с мемоизацией** (`stores/auth.ts`):

```typescript
let pending: Promise<void> | null = null
function ensureReady(): Promise<void> {
  if (ready.value) return Promise.resolve()        // уже знаем — не дёргаем сеть
  if (!pending) {
    pending = apiMe()                              // GET /core-users/auth/me
      .then(_apply)                                // залогинен → ставим user + ability
      .catch(() => _apply(null))                   // 401 → гость
      .finally(() => { ready.value = true; pending = null })
  }
  return pending                                   // burst вызовов делит ОДИН запрос
}
```

`pending` гарантирует, что даже если на первой навигации `ensureReady()` вызовут
пять раз подряд — `/me` уйдёт **один раз**, остальные дождутся той же промис.

Этот `ensureReady()` дёргает router-guard перед каждой навигацией
(`web/src/router/guards.ts`):

```typescript
router.beforeEach(async to => {
  if (to.meta.public && !to.meta.guestOnly) return true   // 404/ошибки — без auth

  const auth = useAuthStore()
  await auth.ensureReady()                                // дождаться /me

  if (to.meta.guestOnly)                                  // /login
    return auth.isLoggedIn ? { path: '/home' } : true     // залогинен → домой
  if (!auth.isLoggedIn)
    return { path: '/login', query: ... }                 // гость → на логин
  return canNavigate(to) ? true : { path: '/403' }        // прав не хватило → 403
})
```

Доступ к маршруту решается по `meta` роута: `public` (без auth вообще), `guestOnly`
(только для гостей — логин), либо `action`+`subject` (проверка прав через CASL). Роуты
без `action/subject` открыты любому залогиненному.

И последний штрих — приложение **монтируется только после** того, как первый `/me`
отработал (`main.ts` ждёт `router.isReady()`), чтобы интерфейс не моргнул «гостевым»
видом до того, как мы узнали, что юзер залогинен. Пока идёт первый `/me`, висит
статичный сплэш из `index.html`.

---

## 9. Logout — гасим с обеих сторон

```python
# api.py
@internal_router.post("/auth/logout")
async def logout(request: Request, response: Response) -> dict[str, bool]:
    raw = request.cookies.get(cfg.session_cookie_name)
    if raw:
        await auth_service.logout(raw)            # удалить строку сессии из БД
    response.delete_cookie(cfg.session_cookie_name, path="/")  # Set-Cookie: sid=; Max-Age=0
    return {"ok": True}
```

Важно, что гасим **в двух местах**: удаляем запись в БД (теперь токен мёртв, даже если
копия cookie где-то осталась) **и** просим браузер выбросить cookie. Удалить только
cookie мало — серверная сессия осталась бы валидной. На фронте стор подчищает себя
даже если запрос упал (`finally`):

```typescript
async function logout(): Promise<void> {
  try { await apiLogout() } finally { _apply(null) }   // user=null, ability сброшен
}
```

---

## 10. Частые заблуждения

- **«Токен лежит в localStorage, надо его прикладывать в Authorization».** Нет. Токена
  в JS нет вообще; cookie уезжает автоматически. Заголовок `Authorization` мы не шлём.
- **«Стор `auth` — это и есть сессия».** Нет. Стор — проекция в памяти, мрёт при
  перезагрузке. Сессия = cookie + строка в БД, переживает перезагрузку.
- **«Раз cookie httpOnly, XSS не страшен».** XSS всё ещё может дёргать API от твоего
  имени (cookie уедет сама). httpOnly спасает лишь от **кражи** токена наружу, не от
  действий в рамках сессии. Защита от XSS — это в первую очередь не вставлять чужой
  HTML/скрипты.
- **«SameSite=Strict ломает вход по ссылке».** В нашем SPA это не проблема (всё
  one-origin), но в общем случае `Strict` не пошлёт cookie при переходе по внешней
  ссылке — для таких сценариев бывает `Lax`. Нам подходит `Strict`.
- **«В БД хранится токен».** Нет — только его SHA-256-хеш. Дамп таблицы сессий не даёт
  угнать сессию.

---

## Короткое резюме

- Сессия **не хранится на фронте**: токен лежит в **httpOnly-cookie** (JS его не
  читает → XSS не украдёт), а состояние сессии — в таблице `core_users_sessions`.
- Cookie несёт **сырой случайный токен**; в БД — его **SHA-256-хеш**. Флаги
  `HttpOnly` + `Secure` + `SameSite=Strict` закрывают XSS-кражу и CSRF — поэтому нет ни
  `Authorization`-заголовка, ни CSRF-токенов.
- Фронт лишь шлёт `fetch` с `credentials: 'same-origin'` — браузер сам прикладывает
  cookie. На каждом запросе бэкенд (`guard_auth` → `session.resolve`) хеширует cookie-
  токен, находит живую сессию, проверяет два TTL (абсолютные 4 ч + idle 15 мин) и кладёт
  пользователя в `request.state.user`.
- Pinia-`auth` store — это **проекция** «кто я + права», восстанавливаемая запросом
  `/me` при старте (один раз, мемоизированно). Сессия её переживает.
- Пароли — Argon2id (memory-hard) с rehash-on-login.
