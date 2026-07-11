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

echo "Мониторинг остановлен."
