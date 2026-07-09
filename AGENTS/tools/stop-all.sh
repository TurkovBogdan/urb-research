#!/usr/bin/env bash
# Kill all app processes: backend/worker (src/app.py + uvicorn), frontend (vite/pnpm).
# Use when IDE didn't clean up, or before a fresh dev-watch start.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Load ports from .env; fall back to defaults if not set
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  SERVER_PORT=$(grep -E '^SERVER_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]' || true)
  VITE_PORT=$(grep -E '^SERVER_VITE_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]' || true)
fi

SERVER_PORT="${SERVER_PORT:-12200}"
VITE_PORT="${VITE_PORT:-12100}"

PORTS=("$SERVER_PORT" "$VITE_PORT")

pkill -TERM -f 'app\.py' 2>/dev/null && echo "killed app.py" || true

for p in "${PORTS[@]}"; do
  fuser -k -TERM "$p/tcp" 2>/dev/null && echo "killed listener on :$p" || true
done

sleep 1

for p in "${PORTS[@]}"; do
  fuser -k -KILL "$p/tcp" 2>/dev/null && echo "force-killed :$p" || true
done

echo "done (backend :$SERVER_PORT, vite :$VITE_PORT)"
