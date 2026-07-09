"""Разовый seed: реальное исследование «Создание системы очередей на Python» в dev-БД.

Данные собраны живыми вызовами search/research (urb-research MCP) и записаны в
research через CRUD модуля: исследование → запросы → документы (саммери +
релевантность) → отчёты. Пишет в dev-БД (sqlite), только INSERT + create_all
(checkfirst) — без деструктива. Запуск: uv run python dev/bench/research/seed_queues_research.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.core.config import Config
from src.core.database import close_database, create_all, init_database
from src.modules.research import models  # noqa: F401 — регистрирует таблицы
from src.modules.research.constants import DOC_FILTERED, DOC_KEPT
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.web_search.crud import page as page_crud


def _relevance_int(value: float | None) -> int | None:
    """Бенч-оценка (0..1) → шкала 1–10 (для демо)."""
    if value is None:
        return None
    return max(1, min(10, round(value * 10)))

TOPIC = "Создание системы очередей на Python"

OVERVIEW = """# Создание системы очередей на Python — общий обзор

Очередь в Python нужна там, где работу нельзя (или не нужно) выполнять синхронно
в основном потоке: фоновые задачи, буферизация между быстрым producer'ом и
медленным consumer'ом, распределение нагрузки. Выбор инструмента определяется тем,
**в одном процессе** нужна очередь или **между процессами/машинами**.

## Выводы

1. **Внутрипроцессная координация → встроенные очереди.** Для producer-consumer в
   рамках одного процесса достаточно стандартной библиотеки: `queue.Queue`
   (потоки) или `asyncio.Queue` (корутины). Bounded-очередь (`maxsize`) даёт
   backpressure «бесплатно», а `task_done()`/`join()` и sentinel-значения —
   аккуратное завершение. Внешняя инфраструктура не нужна.

2. **Фоновые задачи между процессами → брокер + task queue.** Как только задачи
   должны переживать перезапуск, распределяться по воркерам или машинам — нужен
   внешний брокер и библиотека задач. Дефолт — **Celery + Redis**; для строгой
   durability/маршрутизации — RabbitMQ; для простоты — RQ; для лёгкой современной
   альтернативы — Dramatiq.

3. **Брокер выбирается под допустимый режим отказа.** Redis — быстрый дефолт,
   RabbitMQ — надёжные ack/маршрутизация/DLQ, Kafka — распределённый лог для
   высоконагруженного стриминга. Начинать разумно с Redis и мигрировать по мере
   роста требований к доставке.

## Рекомендация

Начать с самого простого уровня, достаточного для задачи: встроенная
`asyncio.Queue`/`queue` для внутрипроцессной работы; при появлении фоновых задач
между процессами — Dramatiq/RQ на Redis, с переходом на Celery + RabbitMQ по мере
роста сложности воркфлоу. Ключевые сквозные принципы — идемпотентность задач,
backpressure (ограниченный размер очереди) и явная обработка ретраев.

_Подробности — в отчётах по трём запросам ниже._
"""

CELERY_REPORT = """# Реализация очереди задач с Celery и Redis

## Введение

Celery — распределённая очередь задач для Python: выносит длительные и ресурсозатратные
операции из основного приложения в фон (отчёты, обработка медиа, парсинг, сбор данных,
DAG-воркфлоу). Redis выступает и брокером сообщений, и бэкендом результатов, что даёт
быструю отзывчивость — приложение не ждёт завершения тяжёлых операций.

## Брокер Redis

Celery требует брокера. Redis хранит задачи в очереди (по умолчанию `celery`, FIFO с
нюансами приоритетов/ETA) и отдаёт их воркерам; первые задачи видно через
`redis-cli lrange celery 0 100`. Для результатов Redis тоже рекомендуется как backend
(альтернативы — RabbitMQ, Memcached, SQLAlchemy). Частая связка: RabbitMQ как транспорт
+ Redis как result backend; при фокусе на Redis оба на нём.

## Воркеры и пул

`celery -A <app> worker` — главный процесс (supervisor) создаёт пул: по умолчанию по
процессу на ядро CPU (процессы, не потоки). Для I/O-bound — `--pool eventlet`/`gevent`.
В проде — несколько очередей и воркеров на них для разделения нагрузки. Очередь живёт в
брокере, не в памяти Celery.

## Ретраи

Автоматические и ручные ретраи: повтор превращает задачу в ETA-задачу и идёт мимо
главной очереди (в `lrange` не видно — важно при отладке). Устойчивость к временным
сбоям.

## Продакшн

Docker Compose для Redis/воркеров/приложения; конфиг в `celery_app.py`, задачи в
`tasks`; тюнинг размера пула, лимитов памяти, мониторинг (Flower). Разделять очереди по
типу задач (в т.ч. периодические через Celery Beat), тестировать поведение ретраев/ETA.

## Заключение

Celery + Redis — надёжная распределённая очередь задач; при правильной настройке
брокера, пула, ретраев и Docker решает задачи любой сложности без потери отзывчивости.

## Источники
- Coffee Web — Создание распределённой очереди задач (Celery + RabbitMQ + Redis)
- Proglib — Django, Celery и Redis: асинхронные и периодические задачи
- Habr — Celery: проясняем неочевидные моменты
- oneuptime.com — How to Build a Job Queue in Python with Celery and Redis
"""

ASYNCIO_REPORT = """# Встроенные очереди Python: asyncio.Queue, producer-consumer, backpressure

## Введение

Модуль asyncio даёт встроенные `Queue`, `LifoQueue`, `PriorityQueue` — основа паттерна
producer-consumer и управления backpressure. Очередь decoupling'ит производителей и
потребителей, работая буфером, когда скорости генерации и обработки не совпадают. Для
синхронного кода аналогично работает модуль `queue` (потокобезопасный).

## Producer-Consumer

Producer кладёт элементы `await queue.put(x)`, consumers в цикле `while True` берут
`await queue.get()`, обрабатывают и вызывают `queue.task_done()`. `await queue.join()`
ждёт завершения всех задач; sentinel-значение (None / «poison pill») сигналит
consumer'ам о graceful shutdown. Запуск через `asyncio.create_task` + `asyncio.gather`.

## Вариации очередей

`Queue` — FIFO, `LifoQueue` — стек (LIFO), `PriorityQueue` — по приоритету (меньше =
выше; задачу оборачивают в dataclass `order=True`, чтобы сравнивалось только поле
приоритета).

## Backpressure

Bounded-очередь (`maxsize`) автоматически создаёт backpressure: `await queue.put()`
блокируется при заполнении, замедляя producer'ов и предотвращая перегрузку. Пара
fast_producer / slow_consumer естественно балансируется.

## Пайплайны и применения

Очереди соединяются в pipeline (output → input: scanner → sorter → packer). В веб-
приложении HTTP-обработчик кладёт заказ в очередь, фоновые consumers шлют email, пишут
логи и в БД — UI остаётся отзывчивым. Полезен мониторинг размера очереди.

## Заключение

`asyncio.Queue` — эффективный встроенный инструмент producer-consumer: неблокирующая
обработка, естественный backpressure через bounded queues, приоритеты. Ключ —
корректно использовать `put()`/`get()`/`join()`/`task_done()` и мониторить размер.

## Источники
- oneuptime.com — How to Build Asyncio Queues in Python
- Real Python — Python's asyncio: A Hands-On Walkthrough
- Data Leads Future — Unleashing the Power of Python Asyncio's Queue
- dev.to — The Queue: Producer-Consumer Patterns and Async Communication
"""

COMPARE_REPORT = """# Сравнение систем очередей для Python: Celery, RQ, Dramatiq и брокеры

## Введение

Очереди задач выносят трудоёмкие операции (email, отчёты, API-запросы) из синхронного
потока. Celery ориентирован на богатую функциональность и планирование, Dramatiq — на
простоту и производительность, RQ — на минимализм для MVP. Брокеры RabbitMQ, Redis,
Kafka обеспечивают доставку сообщений.

## Инструменты

**Celery** — асинхронная распределённая очередь: несколько брокеров (RabbitMQ, Redis),
pre-fork параллелизм, ретраи, цепочки (chains/groups/chords), Django-интеграция, Beat,
мониторинг Flower. Минусы: сложная настройка, больший расход памяти.

**Dramatiq** — лёгкая библиотека с разумными дефолтами (вдохновлена Sidekiq): простой
API, встроенные ретраи, middleware, лучшая производительность/латентность на старте.
Современная альтернатива Celery для новых проектов без нужды во всём наборе Celery.

**RQ (Redis Queue)** — простейшая модель, только Redis; идеален для небольших приложений
и прототипов, ценящих читаемость выше продвинутой оркестрации.

## Брокеры

- **Redis** — быстрый и простой дефолт для большинства (Celery/Dramatiq/RQ); осторожно с
  давлением памяти и политиками вытеснения.
- **RabbitMQ** — durable-очереди, тонкая маршрутизация (topics, priorities, DLQ),
  надёжные ack; больше ops-оверхеда, лучше для строгой durability (силён с Celery).
- **Kafka** — распределённый лог с репликацией и партициями; высокий throughput и
  persistent-хранение, для стриминга и data-pipeline; сложнее для типовых task-queue.

## Выбор

Правило: начинать с Redis; при необходимости строгой маршрутизации / dead-letter /
долговременной durability — переходить на RabbitMQ (Celery). Kafka — для распределённых
высоконагруженных стримов. По инструменту: Celery — enterprise со сложными воркфлоу;
Dramatiq — баланс простоты и эффективности для стартапов/средних I/O-bound проектов; RQ —
MVP. Разумно стартовать с Dramatiq/RQ и мигрировать на Celery по мере роста сложности.

## Источники
- Abilian Innovation Lab — Message Queues
- Medium (Nexumo) — Reliable Python Queues: Celery/Dramatiq/RQ
- judoscale.com — Choosing The Right Python Task Queue
- double.cloud — Kafka vs RabbitMQ
"""

# Сохранённый контент материала (markdown) по URL — то, «что пришло» и что рендерим
# у себя на деталке документа. Заполнен для релевантных (kept); отсеянные оставляем
# без контента (в реальном пайплайне их не скрейпят) → деталка предложит открыть источник.
CONTENTS = {
    "https://oneuptime.com/blog/post/2025-01-06-python-celery-redis-job-queue/view": """# Job Queue на Celery и Redis

`celery_app.py` создаёт приложение с Redis как брокером **и** result-backend:

```python
app = Celery('myapp', broker=os.getenv('CELERY_BROKER_URL'),
             backend=os.getenv('CELERY_RESULT_BACKEND'), include=['tasks'])
```

Продакшн-надёжность через конфиг: `task_acks_late=True` (ack после выполнения),
`worker_prefetch_multiplier=1` (честная раздача под пиками), `task_serializer='json'`
(без pickle), лимиты `task_soft_time_limit`/`task_time_limit`,
`worker_max_tasks_per_child`/`worker_max_memory_per_child`. Задачи — обычные функции
под `@app.task`; очереди разделяются (`high`/`default`) через `task_queues`.""",
    "https://blog.naveenpn.com/implementing-task-queues-in-python-using-celery-and-redis-scalable-background-jobs": """# Task Queues на Celery + Redis

Celery — зрелая библиотека для асинхронных задач и распределённых очередей; с Redis
как брокером тянет миллионы фоновых задач.

- `broker` — куда слать/забирать сообщения задач; `backend` — где хранить результат/статус.
- `@app.task` регистрирует функцию как задачу.
- Воркер: `celery -A tasks worker --loglevel=info`.
- Покрывает ретраи, результаты, периодические задачи (Beat), мониторинг через Flower.""",
    "https://habr.com/ru/articles/686820": """# Celery: неочевидные моменты

- Очередь целиком живёт в Redis (ключ `celery`, FIFO с нюансами приоритетов/ETA);
  первые задачи видно `redis-cli lrange celery 0 100`.
- Главный процесс-supervisor создаёт **пул процессов** (по числу ядер), не потоков.
- Ретраи превращаются в **ETA-задачи** и идут мимо главной очереди — в `lrange` их не
  видно, это частый источник путаницы при отладке.""",
    "https://dev.to/idrisrampurawala/implementing-a-redis-based-task-queue-with-configurable-concurrency-38db": """# Redis-очередь с настраиваемым concurrency

Задачи складываются в **Redis-список**, обрабатываются пачками через Celery Groups.
`TASK_CONCURRENCY_LIMIT` задаёт размер пачки; callback повторно забирает следующую
порцию. Вся выборка обёрнута в лок (`TASK_EXECUTOR_KEY`), чтобы исключить дублирующее
исполнение.""",
    "https://oneuptime.com/blog/post/2026-01-30-python-asyncio-queues/view": """# Asyncio-очереди в Python

Три типа: `Queue` (FIFO), `LifoQueue` (стек), `PriorityQueue` (по приоритету).

Базовый producer-consumer: producer кладёт `await queue.put(item)`, consumer в цикле
`while True` берёт `await queue.get()`, обрабатывает, зовёт `task_done()`.

**Backpressure**: `asyncio.Queue(maxsize=N)` — при заполнении `put()` блокируется,
замедляя producer'а. Для приоритетов элемент оборачивают в `dataclass(order=True)`.""",
    "https://www.dataleadsfuture.com/unleashing-the-power-of-python-asyncios-queue": """# Мощь asyncio.Queue

Когда producer и consumer работают с разной скоростью, очередь выступает **буфером** и
decoupling'ит их. Аналогия супермаркета: покупатели — producers, кассиры — consumers,
очередь покупателей — сама queue.

Плюсы: реализует producer-consumer, контролирует число параллельных задач, делает
потребление ресурсов управляемым и систему — гибко масштабируемой.""",
    "https://realpython.com/async-io-python": """# asyncio: producer-consumer

`producer()` асинхронно получает данные и кладёт каждый элемент в `asyncio.Queue`;
после всех — вставляет **sentinel (poison pill)** на каждого consumer'а для чистого
завершения. `consumer()` читает из очереди, обрабатывает, а получив sentinel — выходит.

Очередь — точка коммуникации producer'ов и consumer'ов, обеспечивающая безопасный и
упорядоченный обмен и параллельную обработку.""",
    "https://gist.github.com/showa-yojyo/4ed200d4c41f496a45a7af2612912df3": """# Минимальный producer/consumer на asyncio.Queue

```python
async def produce(queue, n):
    for x in range(1, n + 1):
        await queue.put(x)

async def consume(queue):
    while True:
        item = await queue.get()
        # ... обработка ...
        queue.task_done()

async def run(n):
    queue = asyncio.Queue()
    consumers = [asyncio.create_task(consume(queue)) for _ in range(3)]
    await produce(queue, n)
    await queue.join()
    for c in consumers:
        c.cancel()
```""",
    "https://lab.abilian.com/Tech/Architecture%20%26%20Software%20Design/Message%20Queues": """# Message Queues — обзор

**Python-задачные очереди:** Celery (RabbitMQ/Redis, богатые фичи, Flower), Dramatiq
(проще, быстрее, middleware), RQ (Redis, минимализм).

**Брокеры:** RabbitMQ (`pika`/`kombu`, AMQP/маршрутизация), Kafka
(`confluent-kafka`, высокий throughput, лог), Redis (`redis-py`, in-memory,
кэш+брокер), ActiveMQ.""",
    "https://medium.com/@Nexumo_/reliable-python-queues-7-celery-dramatiq-rq-choices-266ac544a4a5": """# Надёжные очереди на Python: что выбрать

- **Celery** — богатые фичи (routing, chords/chains, Beat); силён с RabbitMQ.
- **Dramatiq** — лёгкий, производительный, явный middleware.
- **RQ** — простейшая модель, если вы уже на Redis.

Брокер выбирают под допустимый отказ: Redis (быстро, но следить за памятью), RabbitMQ
(durable, маршрутизация, ack), Postgres/SQS (латентность↔durability). Правило: старт с
Redis, при строгой durability/DLQ — RabbitMQ. Ретраи требуют идемпотентности.""",
    "https://judoscale.com/blog/choose-python-task-queue": """# Выбор task queue для Python

**Dramatiq** — библиотека с фокусом на простоте, надёжности и производительности;
поддерживает RabbitMQ и Redis. Похожа на Celery, но намеренно с меньшим набором фич —
встроенного планировщика нет, но его несложно добавить.

Часто это более современная альтернатива Celery для новых проектов, когда весь набор
фич Celery не нужен, а производительность важна.""",
    "https://double.cloud/blog/posts/2023/03/apache-kafka-vs-rabbitmq": """# Kafka vs RabbitMQ

- **RabbitMQ** — классическая очередь: сообщения собираются в queue и раздаются
  consumer'ам; гибкая маршрутизация (point-to-point, pub-sub, request-reply).
- **Kafka** — распределённый publish-subscribe: данные пишутся в topics и в реальном
  времени доставляются consumer'ам; высокий throughput, persistent-лог, строгий порядок.

Kafka лучше по throughput и горизонтальному масштабу и надёжнее хранит (durable log);
RabbitMQ эффективнее на множестве одновременных соединений.""",
}

QUERIES = [
    {
        "text": "Очередь задач на Celery и Redis: брокер, воркеры, ретраи, продакшн-настройки",
        "report": CELERY_REPORT,
        "documents": [
            {
                "url": "https://oneuptime.com/blog/post/2025-01-06-python-celery-redis-job-queue/view",
                "title": "How to Build a Job Queue in Python with Celery and Redis",
                "relevance": 0.95,
                "summary": "Полный гайд: celery_app.py с Redis broker+backend, продакшн-настройки "
                "(task_acks_late, prefetch=1, лимиты памяти, time_limit), именованные очереди.",
            },
            {
                "url": "https://blog.naveenpn.com/implementing-task-queues-in-python-using-celery-and-redis-scalable-background-jobs",
                "title": "Implementing Task Queues in Python Using Celery and Redis",
                "relevance": 0.9,
                "summary": "Как Celery работает под капотом, Redis как брокер, @app.task, запуск "
                "воркера, ретраи/результаты, периодические задачи, деплой (Flower).",
            },
            {
                "url": "https://habr.com/ru/articles/686820",
                "title": "Celery: проясняем неочевидные моменты (Habr)",
                "relevance": 0.85,
                "summary": "Нюансы: очередь целиком в Redis, пул = процессы по числу ядер, ретраи "
                "уходят в ETA-задачи мимо главной очереди (не видно в lrange).",
            },
            {
                "url": "https://dev.to/idrisrampurawala/implementing-a-redis-based-task-queue-with-configurable-concurrency-38db",
                "title": "Implementing a Redis-Based Task Queue with Configurable Concurrency",
                "relevance": 0.7,
                "summary": "Очередь на Redis-списках + Celery Groups с настраиваемым concurrency и "
                "локом, чтобы не было дублей исполнения.",
            },
            {
                "url": "https://stackoverflow.com/questions/60383657/celery-queues-and-redis-queues",
                "title": "Celery queues and Redis queues (Stack Overflow)",
                "relevance": 0.4,
                "filtered": True,
                "filter_reason": "Частный вопрос-ответ, не обзорный материал — дублирует уже "
                "покрытое основными источниками.",
            },
            {
                "url": "https://www.youtube.com/watch?v=0gtdUkEzzn4",
                "title": "Professional Task Queues in Python with Celery, RabbitMQ & Redis (YouTube)",
                "relevance": 0.35,
                "filtered": True,
                "filter_reason": "Видео без текстовой расшифровки — не подходит как цитируемый "
                "текстовый источник отчёта.",
            },
        ],
    },
    {
        "text": "Встроенные очереди в Python: модуль queue и asyncio.Queue, producer-consumer, backpressure",
        "report": ASYNCIO_REPORT,
        "documents": [
            {
                "url": "https://oneuptime.com/blog/post/2026-01-30-python-asyncio-queues/view",
                "title": "How to Build Asyncio Queues in Python",
                "relevance": 0.95,
                "summary": "Три типа (Queue/LifoQueue/PriorityQueue), producer-consumer, bounded "
                "queue для backpressure, sentinel-shutdown, dataclass(order=True) для приоритетов.",
            },
            {
                "url": "https://www.dataleadsfuture.com/unleashing-the-power-of-python-asyncios-queue",
                "title": "Unleashing the Power of Python Asyncio's Queue",
                "relevance": 0.9,
                "summary": "Очередь как буфер между producer/consumer на аналогии супермаркета; "
                "контроль числа параллельных задач и управляемое потребление ресурсов.",
            },
            {
                "url": "https://realpython.com/async-io-python",
                "title": "Python's asyncio: A Hands-On Walkthrough (Real Python)",
                "relevance": 0.85,
                "summary": "Producer кладёт данные в asyncio.Queue, consumers читают; poison pill "
                "для чистого завершения; decoupling и параллельная обработка.",
            },
            {
                "url": "https://gist.github.com/showa-yojyo/4ed200d4c41f496a45a7af2612912df3",
                "title": "Producer/Consumer pattern with asyncio.Queue (GitHub gist)",
                "relevance": 0.7,
                "summary": "Минимальный рабочий пример produce/consume с queue.task_done()+join() и "
                "отменой consumer-задач после завершения.",
            },
            {
                "url": "https://stackoverflow.com/questions/71568584/understanding-producer-consumer-program-with-asyncio",
                "title": "Understanding producer-consumer program with asyncio (Stack Overflow)",
                "relevance": 0.4,
                "filtered": True,
                "filter_reason": "Разбор частной ошибки порядка строк в consumer — узкий кейс, "
                "не обзор паттерна.",
            },
        ],
    },
    {
        "text": "Сравнение систем очередей для Python: Celery, RQ, Dramatiq и брокеры RabbitMQ, Redis, Kafka",
        "report": COMPARE_REPORT,
        "documents": [
            {
                "url": "https://lab.abilian.com/Tech/Architecture%20%26%20Software%20Design/Message%20Queues",
                "title": "Message Queues — Abilian Innovation Lab",
                "relevance": 0.95,
                "summary": "Обзор Python-очередей (Celery/Dramatiq/RQ) и брокеров (RabbitMQ/Kafka/"
                "Redis/ActiveMQ) с сильными сторонами каждого и когда что выбирать.",
            },
            {
                "url": "https://medium.com/@Nexumo_/reliable-python-queues-7-celery-dramatiq-rq-choices-266ac544a4a5",
                "title": "Reliable Python Queues: Celery/Dramatiq/RQ Choices",
                "relevance": 0.9,
                "summary": "Когда что брать (Celery/Dramatiq/RQ), выбор брокера под допустимый режим "
                "отказа, стартовые сниппеты, идемпотентность и at-least-once.",
            },
            {
                "url": "https://judoscale.com/blog/choose-python-task-queue",
                "title": "Choosing The Right Python Task Queue",
                "relevance": 0.8,
                "summary": "Dramatiq как более простая и производительная альтернатива Celery "
                "(RabbitMQ/Redis, без встроенного планировщика), выбор бэкенда-брокера.",
            },
            {
                "url": "https://double.cloud/blog/posts/2023/03/apache-kafka-vs-rabbitmq",
                "title": "Kafka vs. RabbitMQ: Features, Performance, Use Cases",
                "relevance": 0.7,
                "summary": "RabbitMQ (очередь+маршрутизация, point-to-point/pub-sub) против Kafka "
                "(распределённый лог, высокий throughput, persistence) — архитектура и метрики.",
            },
            {
                "url": "https://stackoverflow.com/questions/46517613/python-task-queue-alternatives-and-frameworks",
                "title": "Python task queue alternatives and frameworks (Stack Overflow)",
                "relevance": 0.4,
                "filtered": True,
                "filter_reason": "Тред-обсуждение с частично устаревшими ответами — перекрывается "
                "более свежими обзорами.",
            },
        ],
    },
]


_RESET_TABLES = (
    "research_source_document",
    "research_source_query",
    "research_area",
    "research_index",
)


async def seed() -> None:
    config = Config()
    assert config.db_provider == "sqlite", "seed предназначен только для dev-sqlite"
    engine = await init_database(config)
    try:
        # Идемпотентность + применение изменений схемы (dev одноразовый): сносим
        # только таблицы research и пересобираем их через create_all.
        async with engine.begin() as conn:
            for table in _RESET_TABLES:
                await conn.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
        await create_all(engine)

        research = await research_crud.research_create(title=TOPIC)
        area = await area_crud.area_create(
            research_code=research.code,
            title="Общее",
            description="Все запросы темы под одной областью (демо).",
        )

        for index, spec in enumerate(QUERIES):
            fake_search_code = f"{'0' * 20}{index:02d}"
            query_row = await source_query_crud.source_query_create(
                research_code=research.code,
                area_code=area.code,
                search_code=fake_search_code,
                query=spec["text"],
            )
            for doc in spec["documents"]:
                page = await page_crud.page_upsert(doc["url"], title=doc["title"])
                content = CONTENTS.get(doc["url"])
                if content:
                    await page_crud.page_set_body(page.code, body=content)
                created = await source_document_crud.source_document_create(
                    research_code=research.code,
                    area_code=area.code,
                    query_code=query_row.code,
                    page_code=page.code,
                    summary=doc.get("summary"),
                )
                relevance = _relevance_int(doc.get("relevance"))
                if relevance is not None:
                    await source_document_crud.source_document_set_relevance(
                        created.code, relevance
                    )
                if doc.get("filtered"):
                    await source_document_crud.source_document_set_status(
                        created.code, DOC_FILTERED, doc.get("filter_reason")
                    )
                else:
                    await source_document_crud.source_document_set_status(
                        created.code, DOC_KEPT
                    )
            await source_query_crud.source_query_set_body(query_row.code, spec["report"])

        await research_crud.research_update(research.code, body=OVERVIEW)

        print(
            f"seeded research code={research.code} '{TOPIC}': "
            f"1 area, {len(QUERIES)} queries, "
            f"{sum(len(q['documents']) for q in QUERIES)} documents, "
            f"{len(QUERIES)} query bodies"
        )
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(seed())
