#!/usr/bin/env bash
# Обновление установки: fast-forward на origin/UPDATE_BRANCH, uv sync, копия базы,
# миграции, рестарт. Вся логика — в `src/app.py update` (см. его докстринг и коды выхода).
#
#   ./update.sh            # обновить
#   ./update.sh --dry-run  # напечатать шаги и план остановки процессов, ничего не трогая
#
# `exec` обязателен: он замещает оболочку ДО того, как git перепишет этот файл под ней
# (bash читает скрипт по мере выполнения). `cd` — тоже: `src/app.py` относительный, а
# `uv run` ищет проект от текущей директории.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 1
exec uv run python src/app.py update "$@"
