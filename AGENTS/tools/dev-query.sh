#!/usr/bin/env bash
# Ad-hoc SQL против dev-базы. Бэкенд выбирается по DB_PROVIDER из .env:
# sqlite (dev по умолчанию) → runtime/<APP_ENV>/app.sqlite3, postgres → DB_* креды.
#
#   bash AGENTS/tools/dev-query.sh "SELECT count(*) FROM web_search_page"
#   echo "SELECT * FROM web_search_query LIMIT 5" | bash AGENTS/tools/dev-query.sh
#
# SELECT/WITH/SHOW/EXPLAIN/TABLE/PRAGMA печатаются таблицей; прочее — статусом команды.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export DEV_QUERY_ROOT="$ROOT"

if [ "$#" -gt 0 ]; then
  uv run python AGENTS/tools/dev_query.py "$@"
else
  uv run python AGENTS/tools/dev_query.py
fi
