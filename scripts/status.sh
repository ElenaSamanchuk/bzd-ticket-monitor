#!/bin/bash
# Статус локального мониторинга и GitHub runner
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="by.elenasamanchuk.bzd-ticket-monitor"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

echo "=== Локальный монитор (LaunchAgent) ==="
if [[ -f "$PLIST" ]]; then
  if launchctl print "gui/$(id -u)/$LABEL" &>/dev/null; then
    echo "LaunchAgent: запущен"
  else
    echo "LaunchAgent: установлен, но не активен"
  fi
else
  echo "LaunchAgent: не установлен (запустите scripts/install-launchagent.sh)"
fi

if pgrep -fl "bzd-ticket-monitor/monitor.py" >/dev/null; then
  echo "Процесс monitor.py:"
  pgrep -fl "bzd-ticket-monitor/monitor.py"
else
  echo "Процесс monitor.py: не найден"
fi

if [[ -f "$ROOT/.cache/monitor.log" ]]; then
  echo ""
  echo "Последние строки лога:"
  tail -n 3 "$ROOT/.cache/monitor.log" || true
fi

echo ""
echo "=== GitHub Actions runner (self-hosted) ==="
RUNNER_DIR="$HOME/actions-runner"
RUNNER_LABEL="by.elenasamanchuk.bzd-github-runner"
if [[ -x "$RUNNER_DIR/svc.sh" ]] && "$RUNNER_DIR/svc.sh" status 2>/dev/null | rg -q "active|running"; then
  "$RUNNER_DIR/svc.sh" status || true
elif launchctl print "gui/$(id -u)/$RUNNER_LABEL" &>/dev/null; then
  echo "Runner LaunchAgent: запущен"
  if [[ -f "$RUNNER_DIR/runner.log" ]]; then
    tail -n 2 "$RUNNER_DIR/runner.log" || true
  fi
elif [[ -f "$RUNNER_DIR/.runner" ]]; then
  echo "Runner зарегистрирован, но не запущен. Запустите: scripts/install-github-runner.sh"
else
  echo "Runner не установлен (scripts/install-github-runner.sh)"
fi
