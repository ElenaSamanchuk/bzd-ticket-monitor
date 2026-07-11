# Настройка уведомлений и автозапуска

## 1. Telegram

1. Откройте [@BotFather](https://t.me/BotFather) → `/newbot` → имя, например `BZD Tickets Alert`
2. Скопируйте **токен** (вида `123456789:AAH...`)
3. Откройте **вашего нового бота** и нажмите **Start** / напишите `привет`
4. Узнайте chat_id: откройте в браузере  
   `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`  
   Найдите `"chat":{"id":123456789` — это **TELEGRAM_CHAT_ID**

> Ссылка https://t.me/ElaneDmitrievna — это ваш профиль. Бот пишет только после Start, по **числовому** chat_id.

## 2. Gmail (пароль приложения)

1. Google аккаунт → Безопасность → **Двухэтапная аутентификация** (включить)
2. Пароли приложений → создать для «Почта» / «Другое»
3. Скопировать 16-значный пароль

## 3. Секреты в GitHub

В терминале (подставьте свои значения):

```bash
cd ~/Scripts/bzd-ticket-monitor

gh secret set TELEGRAM_BOT_TOKEN --body "ВАШ_ТОКЕН_ОТ_BOTFATHER"
gh secret set TELEGRAM_CHAT_ID --body "ВАШ_CHAT_ID"
gh secret set SMTP_PASSWORD --body "ВАШ_ПАРОЛЬ_ПРИЛОЖЕНИЯ_GMAIL"
```

Или: GitHub → репозиторий → **Settings → Secrets and variables → Actions**

## 4. GitHub Actions (self-hosted на Mac)

Облачный `ubuntu-latest` **не работает** — pass.rw.by отдаёт 403.  
Нужен runner на вашем Mac:

```bash
cd ~/Scripts/bzd-ticket-monitor
./scripts/install-github-runner.sh
```

После установки в GitHub → **Settings → Actions → Runners** появится `mac-home` (Idle).

Workflow использует общий файл состояния с локальным монитором:
`/Users/elena/Scripts/bzd-ticket-monitor/.cache/notified.json`

## 5. Автозапуск после перезагрузки

```bash
./scripts/install-launchagent.sh   # локальный монитор каждые 3 мин
./scripts/status.sh                # проверить, что всё работает
```

## 6. Проверка

```bash
gh workflow run monitor.yml
gh run list --workflow=monitor.yml --limit 3
```

При появлении мест на 707Б или 757Б (13.07.2026) придёт Telegram + письмо на elenasamanchuk@gmail.com.

## Локально (опционально)

```bash
cp config.env.example config.env
# заполните config.env
python3 monitor.py
```
