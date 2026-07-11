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
caffeinate -i python3 monitor.py
```

Остановка: `Ctrl+C`

## Текущий статус (на момент создания)

На 13.07.2026 поезда **707Б** и **757Б**: **мест нет** — скрипт будет ждать отказники.

## Notion

Нативной отправки в Notion нет. Проще Telegram или почта. Notion можно подключить через Zapier/Make, если очень нужно.
