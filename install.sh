#!/usr/bin/env bash
# Первый запуск установки: проверить инструменты, поставить зависимости, запустить приложение.
#
#   git clone https://github.com/TurkovBogdan/urb-research && cd urb-research
#   ./install.sh
#
# Скрипт настраивает то дерево, в котором лежит. Повторный запуск безопасен: зависимости
# синхронизируются заново, приложение поднимается. `.env` и схему базы создаёт сам первый
# старт (`src/app.py`), поэтому отдельного шага настройки тут нет.
set -euo pipefail
cd "$(dirname "$0")"

UV_INSTALLER_URL="https://astral.sh/uv/install.sh"
UV_PATH_SNIPPET="$HOME/.local/bin/env"

die() {
  echo "install.sh: $1" >&2
  exit 1
}

require_checkout() {
  [[ -f src/app.py ]] ||
    die "рядом нет src/app.py — запускайте скрипт из склонированного репозитория"
}

# Системные пакеты под sudo скрипт не ставит: это решение владельца машины, а не установщика.
require_git() {
  command -v git >/dev/null 2>&1 && return 0
  die "нужен git — поставьте его менеджером пакетов (Debian/Ubuntu: sudo apt-get install -y git; macOS: brew install git)"
}

# Спрашиваем только человека за терминалом: в конвейере (cron, CI) молчание — это не «да».
confirmed() {
  [[ -t 0 ]] || return 1
  local answer
  read -r -p "$1 [y/N] " answer
  [[ "$answer" == [yY] ]]
}

ensure_uv() {
  command -v uv >/dev/null 2>&1 && return 0
  echo "uv не найден — это менеджер проекта, он же скачивает Python 3.12."
  echo "Официальный установщик: curl -LsSf $UV_INSTALLER_URL | sh"
  confirmed "Поставить uv сейчас?" ||
    die "без uv установка не пойдёт — поставьте его и запустите скрипт снова"
  curl -LsSf "$UV_INSTALLER_URL" | sh
  # Установщик кладёт бинарь в ~/.local/bin, но PATH этой оболочки уже собран — без
  # подхвата следующая же строка своего же uv не нашла бы.
  if [[ -f "$UV_PATH_SNIPPET" ]]; then
    # shellcheck source=/dev/null
    source "$UV_PATH_SNIPPET"
  fi
  command -v uv >/dev/null 2>&1 ||
    die "uv поставлен, но не виден в PATH — перелогиньтесь и запустите скрипт снова"
}

# Печатается ДО старта: дальше терминал занят работающим приложением, и подсказка уедет
# за пределы экрана вместе с логом.
announce_next_steps() {
  cat <<'EOF'

Зависимости на месте. Первый старт создаст .env с секретами установки и развернёт пустую базу.
Браузер откроется на странице «Сервер» — там правятся параметры установки (порт, база, режим).
Дальше в интерфейсе:

  «Интеграции»  — ключ поискового сервиса; хватит одного, по умолчанию это Tavily
  «MCP-серверы» — готовый конфиг подключения для MCP-клиента

Остановить: ./run.sh stop     Обновить: ./update.sh

EOF
}

require_checkout
require_git
ensure_uv
# --all-groups: тот же набор, что синхронизирует обновление, иначе первое же `./update.sh`
# переставит окружение заново.
uv sync --all-groups
announce_next_steps
# Установка заканчивается не главной страницей, а настройками установки: первое, что человек
# решает после первого старта, — оставить ли порт, базу и режим такими, какими их выписал `.env`.
RUN_OPEN_PATH=/settings/core exec ./run.sh
