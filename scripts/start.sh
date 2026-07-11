#!/bin/bash
# Запуск локального мониторинга (каждые 3 мин, Mac не уснёт)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p .cache
export STATE_FILE="${STATE_FILE:-$ROOT/.cache/notified.json}"

exec caffeinate -i python3 "$ROOT/monitor.py"
