#!/bin/bash
# Полное отключение мониторинга: автозапуск, процессы, GitHub runner
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"

stop_launchagent() {
  local label="$1"
  local plist="$HOME/Library/LaunchAgents/${label}.plist"
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || launchctl unload "$plist" 2>/dev/null || true
  rm -f "$plist"
}

echo "Останавливаю локальный монитор..."
stop_launchagent "by.elenasamanchuk.bzd-ticket-monitor"
pkill -f "caffeinate -i python3 .*bzd-ticket-monitor/monitor.py" 2>/dev/null || true
pkill -f "python3 .*bzd-ticket-monitor/monitor.py" 2>/dev/null || true

echo "Останавливаю GitHub runner..."
stop_launchagent "by.elenasamanchuk.bzd-github-runner"
pkill -f "actions-runner.*Runner.Listener" 2>/dev/null || true
pkill -f "$RUNNER_DIR/run.sh" 2>/dev/null || true

if [[ -x "$RUNNER_DIR/svc.sh" ]]; then
  sudo "$RUNNER_DIR/svc.sh" stop 2>/dev/null || true
  sudo "$RUNNER_DIR/svc.sh" uninstall 2>/dev/null || true
fi

if [[ -f "$RUNNER_DIR/.runner" ]] && [[ -x "$RUNNER_DIR/config.sh" ]]; then
  echo "Снимаю runner с GitHub (нужен gh и интернет)..."
  TOKEN="$(gh api repos/ElenaSamanchuk/bzd-ticket-monitor/actions/runners/remove-token -X POST --jq .token 2>/dev/null || true)"
  if [[ -n "$TOKEN" ]]; then
    cd "$RUNNER_DIR"
    ./config.sh remove --token "$TOKEN" || true
  fi
fi

echo ""
echo "Готово. Автозапуск отключён, процессы остановлены."
echo ""
echo "Опционально:"
echo "  • Отключить cron в GitHub: закомментируйте schedule в .github/workflows/monitor.yml"
echo "  • Удалить папку runner: rm -rf $RUNNER_DIR"
echo "  • Проверка: $ROOT/scripts/status.sh"
