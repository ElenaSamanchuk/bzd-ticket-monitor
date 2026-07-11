# Монитор билетов БЖД (707Б / 757Б, 13.07.2026)

Проверяет [pass.rw.by](https://pass.rw.by) каждые 3 минуты и шлёт оповещение, когда появляются места.

## Быстрый старт

```bash
cd ~/Scripts/bzd-ticket-monitor
python3 monitor.py
```

Пока скрипт запущен — при появлении билетов:
- звук + уведомление macOS
- сообщение в Telegram (если настроен `config.env`)
- письмо на почту (если настроен SMTP)

## Telegram (5 минут)

```bash
cp config.env.example config.env
# заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID
python3 monitor.py
```

## Запуск на ночь (Mac не уснёт)

```bash
cd ~/Scripts/bzd-ticket-monitor
./scripts/start.sh
```

Остановка: `Ctrl+C` или `./scripts/stop.sh`

## Автозапуск после перезагрузки Mac

Один раз установите LaunchAgent — дальше мониторинг стартует сам при входе в систему:

```bash
cd ~/Scripts/bzd-ticket-monitor
./scripts/install-launchagent.sh
```

Проверка: `./scripts/status.sh`  
Остановка: `./scripts/stop.sh`  
Перезапуск вручную: `./scripts/stop.sh && ./scripts/install-launchagent.sh`  
**Полное отключение** (когда билеты куплены): `./scripts/uninstall.sh`

Логи: `.cache/monitor.log` и `.cache/monitor.err.log`

## GitHub Actions (24/7, Mac может спать)

pass.rw.by блокирует облако GitHub напрямую, но через **staronki.by** проверка работает автономно.

```bash
gh workflow run monitor.yml --repo ElenaSamanchuk/bzd-ticket-monitor
```

Подробнее: **AUTONOMOUS.md** и **SETUP.md**

Локальный Mac и self-hosted runner **не нужны**. Чтобы не было дублей:

```bash
./scripts/uninstall.sh
```

## Текущий статус (на момент создания)

На 13.07.2026 поезда **707Б** и **757Б**: **мест нет** — скрипт будет ждать отказники.

## Notion

Нативной отправки в Notion нет. Проще Telegram или почта. Notion можно подключить через Zapier/Make, если очень нужно.
