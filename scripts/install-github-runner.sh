#!/bin/bash
# Self-hosted runner на этом Mac — pass.rw.by видит домашний IP, не блокирует как GitHub cloud
set -euo pipefail

REPO="ElenaSamanchuk/bzd-ticket-monitor"
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"
RUNNER_NAME="${RUNNER_NAME:-mac-home}"
ARCH="$(uname -m)"

case "$ARCH" in
  arm64) RUNNER_ARCH="arm64" ;;
  x86_64) RUNNER_ARCH="x64" ;;
  *) echo "Неподдерживаемая архитектура: $ARCH"; exit 1 ;;
esac

RUNNER_VERSION="${RUNNER_VERSION:-2.327.1}"
TARBALL="actions-runner-osx-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"

echo "Репозиторий: $REPO"
echo "Папка runner: $RUNNER_DIR"

if [[ -x "$RUNNER_DIR/config.sh" ]] && [[ -x "$RUNNER_DIR/run.sh" ]]; then
  echo "Runner уже установлен в $RUNNER_DIR"
else
  mkdir -p "$RUNNER_DIR"
  cd "$RUNNER_DIR"
  echo "Скачиваю $URL ..."
  curl -fsSL -o "$TARBALL" "$URL"
  tar xzf "$TARBALL"
  rm -f "$TARBALL"
fi

cd "$RUNNER_DIR"

if [[ ! -f .runner ]]; then
  echo "Получаю registration token..."
  TOKEN="$(gh api "repos/${REPO}/actions/runners/registration-token" -X POST --jq .token)"
  ./config.sh \
    --url "https://github.com/${REPO}" \
    --token "$TOKEN" \
    --name "$RUNNER_NAME" \
    --unattended \
    --replace
else
  echo "Runner уже зарегистрирован ($(cat .runner 2>/dev/null || echo 'ok'))"
fi

echo "Устанавливаю службу (автозапуск после перезагрузки)..."
if sudo ./svc.sh install && sudo ./svc.sh start; then
  ./svc.sh status || true
  echo ""
  echo "Готово (системная служба). В GitHub: Settings → Actions → Runners"
else
  echo ""
  echo "sudo недоступен — ставлю LaunchAgent без пароля..."
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  LABEL="by.elenasamanchuk.bzd-github-runner"
  PLIST_SRC="$ROOT/com.elenasamanchuk.bzd-github-runner.plist"
  PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
  sed "s|__RUNNER_DIR__|$RUNNER_DIR|g" "$PLIST_SRC" > "$PLIST_DST"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
  echo "Готово (LaunchAgent). Лог: $RUNNER_DIR/runner.log"
fi

echo "Workflow: runs-on: self-hosted"
