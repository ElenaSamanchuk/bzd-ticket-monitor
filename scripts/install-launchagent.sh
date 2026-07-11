#!/bin/bash
# Автозапуск мониторинга после входа в macOS (перезагрузка / логин)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="by.elenasamanchuk.bzd-ticket-monitor"
PLIST_SRC="$ROOT/com.elenasamanchuk.bzd-ticket-monitor.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
START_SCRIPT="$ROOT/scripts/start.sh"

chmod +x "$START_SCRIPT" "$ROOT/scripts/stop.sh" "$ROOT/scripts/status.sh"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/.cache"

sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" > "$PLIST_DST"

# Перезапуск, если уже был загружен
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"

echo "Готово. Мониторинг запустится автоматически после входа в систему."
echo "Проверка: $ROOT/scripts/status.sh"
echo "Остановка: $ROOT/scripts/stop.sh"
