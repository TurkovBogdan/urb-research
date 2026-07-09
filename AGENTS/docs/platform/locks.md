# core/locks — распределённые локи

Поверх таблицы `core_locks`. Один файл `src/core/locks/lock.py` содержит:

- `CoreLockRow` — ORM-модель строки таблицы.
- `CoreLock` — высокоуровневая обёртка с фабричным методом `acquire`.
- `release_for_owners(owners)` — bulk-cleanup для zombie-задач.

## Создание лока

```python
from src.core.locks import CoreLock

lock = await CoreLock.acquire("hh:sync", 300)  # ttl — секунды
if lock is None:
    return  # кто-то уже держит лок
# ... делаем работу под локом ...
```

`owner` можно задать явно (например, `task_run:42`), иначе генерируется ULID. Если за `ttl` секунд лок не сняли — его может перехватить другой `acquire`.

## Снятие лока

```python
await lock.release()
```

`release` снимает лок, только если мы всё ещё владелец. Если за это время лок протух и его перехватил другой owner — `release` вернёт `False` и чужую запись не тронет.

## Проверка владения

```python
if not await lock.is_owner():
    return  # лок протух, нас перехватили
```

Fencing-проверка перед критическими операциями.

## Продление TTL

```python
if not await lock.extend(300):
    return  # лок уже не наш — продлить нечего
```

`extend` сначала проверяет владение, затем UPDATE-ит `expires_at`.

## Принудительное снятие (без owner)

```python
await CoreLock.force_release("hh:browser")
```

DELETE по ключу без проверки владельца. Использовать только для аварийной очистки зависших локов (например, браузерная сессия потеряна, но лок в БД остался).

## Внутри scheduler-задач

Runner в `finally` снимает все локи задачи автоматически (`release_for_owners` по `owner = task_run:{task_id}`). `release` можно не вызывать явно — это страховка от забытого вызова и падений:

```python
async def my_task(ctx):
    lock = await CoreLock.acquire("hh:sync", 300, owner=ctx.lock.owner)
    if lock is None:
        return
    # ... работаем ...
    # release можно не звать — runner подчистит
```
