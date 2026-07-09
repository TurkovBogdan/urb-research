#!/usr/bin/env bash
# Restart the FastAPI backend (uvicorn on src.apps.app.server:app, --reload).
# Use after editing Python source that the backend imports (modules, CRUD, API).
# Vite is managed by the IDE — this script does not touch it.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Read SERVER_PORT from .env (fallback to 13410)
PORT=$(grep -E '^SERVER_PORT=' "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || echo "13410")

# Kill whatever is listening on the port
pid=$(fuser "$PORT/tcp" 2>/dev/null | tr -s ' ' '\n' | grep -v '^$' | head -1 || true)

if [ -n "$pid" ]; then
  kill -TERM "$pid" 2>/dev/null || true
  sleep 0.5
  kill -KILL "$pid" 2>/dev/null || true
  echo "Killed PID $pid on :$PORT"
fi

# Start uvicorn in background
cd "$PROJECT_ROOT"
set -a; source "$PROJECT_ROOT/.env"; set +a
uv run uvicorn src.apps.app.server:app \
  --host "${SERVER_HOST:-127.0.0.1}" --port "$PORT" --reload \
  >> /tmp/hh-server.log 2>&1 &

echo "Backend starting on :$PORT (PID $!). Log: /tmp/hh-server.log"
echo "Run: curl http://localhost:$PORT/internal/health to verify."
