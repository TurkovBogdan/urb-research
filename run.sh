#!/usr/bin/env bash
# Запуск проекта: без аргументов — запуск на собранном фронте, dev (Vite + backend hot-reload),
# build-prod (сборка фронта), stop (гашение), test (pytest).
# Порты и провайдер БД берутся из .env (SERVER_PORT, SERVER_VITE_PORT, DB_PROVIDER).
set -euo pipefail
cd "$(dirname "$0")"

if command -v pnpm >/dev/null 2>&1; then
  PNPM=(pnpm)
else
  PNPM=(corepack pnpm)
fi

usage() {
  cat <<'EOF'
run.sh — запуск проекта

  ./run.sh             backend (--backend --worker) + открытие веб-интерфейса в браузере;
                       фронт раздаётся собранным из web/dist, hot-reload нет
  ./run.sh dev         front (Vite HMR) + backend (--backend --worker --hot-reload)
  ./run.sh build-prod  собрать фронт в боевом режиме в web/dist (нужны Node.js 20+ и pnpm)
  ./run.sh stop        погасить установку по реестру процессов (src/app.py stop, аргументы
                       пробрасываются) плюс Vite по SERVER_VITE_PORT из .env
  ./run.sh test        uv run pytest — аргументы пробрасываются (./run.sh test --core)
  ./run.sh help        эта справка

Сборка фронта — отдельная команда: web/dist лежит в репозитории, и установке достаточно
`git pull`, поэтому запуск ничего не собирает (`./run.sh prod` = запуск без сборки).
Адрес backend'а берётся из .env (SERVER_HOST/SERVER_PORT), Vite печатает свой при старте.
EOF
}

# Адрес и готовность спрашиваем у самого приложения теми же функциями, что и MCP-шим: порт у
# каждой установки свой, а браузер, открытый до первого ответа, показывает ошибку соединения.
# Отвечающий заглушкой backend (отставшая схема) тоже открывается — заглушка и есть ответ.
# Страница задаётся снаружи (RUN_OPEN_PATH): установщику нужна не главная, а «Сервер».
open_page_when_serving() {
  uv run python - "${RUN_OPEN_PATH:-/}" <<'PY'
import sys
import webbrowser

sys.path.insert(0, ".")

from src.core.backend_launch import base_url, wait_until_ready
from src.core.config import Config

BOOT_TIMEOUT_SECONDS = 120

page = sys.argv[1]
config = Config()
address = base_url(config)
if wait_until_ready(config, timeout=BOOT_TIMEOUT_SECONDS) is None:
    print(f"run.sh: {address} не ответил за {BOOT_TIMEOUT_SECONDS} с — браузер не открываю")
else:
    webbrowser.open(address + page)
PY
}

cmd="${1:-run}"
shift 2>/dev/null || true

case "$cmd" in
  run | prod)
    open_page_when_serving &
    opener_pid=$!
    trap 'kill "$opener_pid" 2>/dev/null || true' EXIT INT TERM
    # `--no-hot-reload` явно: в dev-`.env` стоит SERVER_HOT_RELOAD=true, и без флага эта команда
    # молча поднимала бы сторож правок вместо обещанного запуска на собранном фронте.
    uv run python src/app.py --backend --worker --no-hot-reload
    ;;
  dev)
    "${PNPM[@]}" --dir web dev &
    vite_pid=$!
    trap 'kill "$vite_pid" 2>/dev/null || true' EXIT INT TERM
    uv run python src/app.py --backend --worker --hot-reload
    ;;
  build-prod)
    "${PNPM[@]}" --dir web build
    ;;
  stop)
    # backend/worker — по реестру процессов установки (`runtime/processes/`): гасится ровно
    # этот чекаут, группой и с доказательством смерти. Отбор по имени процесса тут был неверен
    # по существу: шаблон `app.py` ловит и соседнюю установку, и MCP-шимы, и сессию агента.
    # Аргументы пробрасываются: ./run.sh stop --dry-run, ./run.sh stop --stop-unregistered.
    stop_code=0
    uv run python src/app.py stop "$@" || stop_code=$?
    # Vite о себе записи не ведёт — он не процесс приложения, поэтому только он и остаётся за
    # портом из .env. Порт не угадывается: на установке Vite нет вовсе, а на угаданном номере
    # может слушать чужой процесс. Сухой прогон не трогает и его — «показать план» не гасит.
    vite_port=$(grep -E '^SERVER_VITE_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)
    if [[ -z "$vite_port" ]]; then
      echo "SERVER_VITE_PORT в .env не задан — Vite не ищу"
    elif [[ " $* " == *" --dry-run "* ]]; then
      echo "vite on :$vite_port left alone (--dry-run)"
    else
      fuser -k -TERM "$vite_port/tcp" 2>/dev/null && echo "stopped vite on :$vite_port" || true
    fi
    exit "$stop_code"
    ;;
  test)
    uv run pytest "$@"
    ;;
  help | -h | --help)
    usage
    ;;
  *)
    echo "unknown command: $cmd" >&2
    usage
    exit 1
    ;;
esac
