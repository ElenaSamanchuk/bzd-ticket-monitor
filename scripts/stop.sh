#!/bin/bash
# Остановка локального мониторинга (LaunchAgent + ручной запуск)
set -euo pipefail

LABEL="by.elenasamanchuk.bzd-ticket-monitor"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [[ -f "$PLIST" ]]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null || true
fi

pkill -f "caffeinate -i python3 .*bzd-ticket-monitor/monitor.py" 2>/dev/null || true
pkill -f "python3 .*bzd-ticket-monitor/monitor.py" 2>/dev/null || true

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for pid in $(pgrep -f "monitor.py" 2>/dev/null || true); do
  cwd="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
  if [[ "$cwd" == "$ROOT" ]]; then
    kill "$pid" 2>/dev/null || true
  fi
done

echo "Мониторинг остановлен."
