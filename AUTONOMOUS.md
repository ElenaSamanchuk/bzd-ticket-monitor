# Автономный мониторинг (Mac выключен)

Оба сервиса работают через **GitHub Actions** в облаке — Mac может спать или быть выключен.

| Монитор | Репозиторий | Как работает в облаке |
|---------|-------------|----------------------|
| **Вакансии hh.ru** | [hh-vacancy-monitor](https://github.com/ElenaSamanchuk/hh-vacancy-monitor) | Прямой JSON API hh.ru |
| **Билеты БЖД** | [bzd-ticket-monitor](https://github.com/ElenaSamanchuk/bzd-ticket-monitor) | Через staronki.by → pass.rw.by |

## Что отключить на Mac (чтобы не было дублей)

```bash
# билеты
cd ~/Scripts/bzd-ticket-monitor && ./scripts/uninstall.sh

# вакансии
cd ~/Scripts/hh-vacancy-monitor && ./scripts/uninstall.sh
```

Self-hosted runner для билетов тоже можно снять — он больше не нужен.

## Проверка

```bash
gh run list --repo ElenaSamanchuk/hh-vacancy-monitor --limit 2
gh run list --repo ElenaSamanchuk/bzd-ticket-monitor --limit 2
```

Оба workflow запускаются **каждые 5 минут** по cron.
