#!/usr/bin/env bash
# Запуск проекта: dev (Vite + backend hot-reload), prod (сборка + backend), test (pytest).
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

  ./run.sh dev    front (Vite HMR :12100) + backend (--backend --worker --hot-reload :12200)
  ./run.sh prod   сборка фронта в web/dist + backend (--backend --worker); фронт раздаёт ядро
  ./run.sh stop   погасить backend/worker (app.py) и Vite; порты из .env, иначе дефолты
  ./run.sh test   uv run pytest — аргументы пробрасываются (./run.sh test --core)
  ./run.sh help   эта справка

Открывать: dev → http://localhost:12100 (Vite), prod → http://localhost:12200 (backend).
EOF
}

cmd="${1:-help}"
shift 2>/dev/null || true

case "$cmd" in
  dev)
    "${PNPM[@]}" --dir web dev &
    vite_pid=$!
    trap 'kill "$vite_pid" 2>/dev/null || true' EXIT INT TERM
    uv run python src/app.py --backend --worker --hot-reload
    ;;
  prod)
    "${PNPM[@]}" --dir web build
    uv run python src/app.py --backend --worker
    ;;
  stop)
    # порты из .env, иначе дефолты (backend 13410, Vite 12100)
    server_port=$(grep -E '^SERVER_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)
    vite_port=$(grep -E '^SERVER_VITE_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)
    server_port="${server_port:-13410}"
    vite_port="${vite_port:-12100}"
    # backend/worker — по имени процесса, не зависит от порта
    pkill -TERM -f 'app\.py' 2>/dev/null && echo "stopped backend/worker (app.py)" || true
    # слушатели портов (backend + Vite): TERM, затем добить KILL
    for port in "$server_port" "$vite_port"; do
      fuser -k -TERM "$port/tcp" 2>/dev/null && echo "stopped listener on :$port" || true
    done
    sleep 1
    for port in "$server_port" "$vite_port"; do
      fuser -k -KILL "$port/tcp" 2>/dev/null || true
    done
    echo "stopped (backend :$server_port, vite :$vite_port)"
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
