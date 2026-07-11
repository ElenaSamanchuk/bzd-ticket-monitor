#!/usr/bin/env python3
"""Мониторинг билетов БЖД на pass.rw.by для конкретных поездов."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import smtplib
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

# --- настройки по умолчанию (можно переопределить через config.env) ---
FROM_STATION = "Гомель"
TO_STATION = "Минск-Пассажирский"
DATE = "13.07.2026"
TRAINS = ("707Б", "757Б")
CHECK_INTERVAL_SEC = 180  # каждые 3 минуты
TZ = ZoneInfo("Europe/Minsk")
STOP_AFTER = datetime(2026, 7, 13, 8, 0, tzinfo=TZ)  # утром 13.07 остановиться

ROUTE_URL = "https://pass.rw.by/ru/route/"
STARONKI_URL = "https://staronki.by"
STARONKI_POLL_SEC = 3
STARONKI_SETUP_TIMEOUT_SEC = 45
_DEFAULT_UA_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
_DEFAULT_UA_LINUX = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
USER_AGENT = os.environ.get(
    "BZD_USER_AGENT",
    _DEFAULT_UA_MAC if sys.platform == "darwin" else _DEFAULT_UA_LINUX,
)
FETCH_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://pass.rw.by/ru/route/",
}


def use_staronki() -> bool:
    if os.environ.get("BZD_USE_STARONKI") == "1":
        return True
    if os.environ.get("BZD_USE_STARONKI") == "0":
        return False
    return os.environ.get("CI") == "true"


def route_search_url() -> str:
    params = urllib.parse.urlencode(
        {"from": FROM_STATION, "to": TO_STATION, "date": DATE}
    )
    return f"{ROUTE_URL}?{params}"


class StaronkiClient:
    """Проверка через staronki.by — их серверы в РБ видят pass.rw.by (для GitHub cloud)."""

    def __init__(self, cookie_file: Path) -> None:
        self.cookie_file = cookie_file
        self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
        self.jar = http.cookiejar.MozillaCookieJar(str(cookie_file))
        if cookie_file.exists():
            try:
                self.jar.load(ignore_discard=True, ignore_expires=True)
            except OSError:
                pass
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def save(self) -> None:
        self.jar.save(ignore_discard=True, ignore_expires=True)

    def _request(self, url: str, data: dict[str, str] | None = None) -> bytes:
        headers = {"User-Agent": USER_AGENT}
        if data is None:
            req = urllib.request.Request(url, headers=headers)
        else:
            body = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with self.opener.open(req, timeout=30) as resp:
            return resp.read()

    def status(self) -> dict:
        raw = self._request(f"{STARONKI_URL}/check_status.php")
        return json.loads(raw.decode("utf-8"))

    def submit_route(self, route_url: str) -> None:
        self._request(f"{STARONKI_URL}/trains.php", {"url": route_url})

    def select_train(self, train: str, saved_url: str) -> None:
        self._request(
            f"{STARONKI_URL}/trains.php",
            {"select_train": train, "saved_url": saved_url},
        )

    def wait_for_trains(self) -> dict:
        deadline = time.time() + STARONKI_SETUP_TIMEOUT_SEC
        while time.time() < deadline:
            data = self.status()
            if data.get("status") == "trains_found" and data.get("trains_list"):
                return data
            if data.get("error_msg"):
                raise RuntimeError(f"staronki.by: {data['error_msg']}")
            time.sleep(STARONKI_POLL_SEC)
        raise RuntimeError("staronki.by: таймаут ожидания списка поездов")

    def ensure_monitoring(self) -> None:
        route_url = route_search_url()
        data = self.status()
        active = {
            task["train_number"]
            for task in data.get("tasks", [])
            if task.get("status") == "monitoring"
            and route_url in (task.get("url") or "")
            and task.get("train_number") in TRAINS
            and int(task.get("remains") or 0) > 3
        }
        missing = [train for train in TRAINS if train not in active]
        if not missing:
            return

        self.submit_route(route_url)
        found = self.wait_for_trains()
        saved_url = found.get("url") or route_url
        available = {item["number"] for item in found.get("trains_list", [])}
        for train in missing:
            if train in available:
                self.select_train(train, saved_url)
                time.sleep(1)

    def availability(self) -> dict[str, dict[str, str | bool]]:
        self.ensure_monitoring()
        data = self.status()
        route_url = route_search_url()
        result: dict[str, dict[str, str | bool]] = {}

        for train in TRAINS:
            result[train] = {
                "selling_allowed": False,
                "no_seats": True,
                "available": False,
                "log": "нет активной задачи",
            }

        for task in data.get("tasks", []):
            train = task.get("train_number")
            if train not in TRAINS or route_url not in (task.get("url") or ""):
                continue
            if task.get("status") != "monitoring":
                continue
            log = task.get("last_log") or ""
            waiting = "Ожидание" in log
            no_seats = "Мест нет" in log
            available = not waiting and not no_seats and "мониторинг завершен" not in log
            result[train] = {
                "selling_allowed": True,
                "no_seats": no_seats or waiting,
                "available": available,
                "log": log,
            }
        return result


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_route_html() -> str:
    params = urllib.parse.urlencode(
        {"from": FROM_STATION, "to": TO_STATION, "date": DATE}
    )
    req = urllib.request.Request(
        f"{ROUTE_URL}?{params}",
        headers=FETCH_HEADERS,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_availability(html: str) -> dict[str, dict[str, str | bool]]:
    """Возвращает статус по каждому поезду из TRAINS."""
    result: dict[str, dict[str, str | bool]] = {}
    row_re = re.compile(
        r'<div class="sch-table__row"[^>]*data-ticket_selling_allowed="(true|false)"'
        r'[^>]*data-train-number="([^"]+)"',
        re.DOTALL,
    )
    for allowed, train in row_re.findall(html):
        if train not in TRAINS:
            continue
        chunk_match = re.search(
            rf'data-train-number="{re.escape(train)}".*?(?=data-train-number=|</body>)',
            html,
            re.DOTALL,
        )
        chunk = chunk_match.group(0) if chunk_match else ""
        no_seats = "Мест нет" in chunk
        result[train] = {
            "selling_allowed": allowed == "true",
            "no_seats": no_seats,
            "available": allowed == "true" and not no_seats,
        }
    for train in TRAINS:
        result.setdefault(train, {"selling_allowed": False, "no_seats": True, "available": False})
    return result


def notify_macos(title: str, message: str) -> None:
    script = f'display notification {json.dumps(message)} with title {json.dumps(title)} sound name "Glass"'
    subprocess.run(["osascript", "-e", script], check=False)


def notify_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": message, "disable_web_page_preview": "true"}
    ).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20):
        pass


def notify_email(subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("EMAIL_TO")
    from_addr = os.environ.get("EMAIL_FROM", user or "")
    if not all([host, user, password, to_addr]):
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())


def buy_link(train: str) -> str:
    params = urllib.parse.urlencode(
        {
            "train": train,
            "from_exp": "2100100",
            "to_exp": "2100001",
            "date": DATE,
            "from": FROM_STATION,
            "to": TO_STATION,
        }
    )
    return f"https://pass.rw.by/ru/train/?{params}"


def notify_all(title: str, body: str) -> None:
    print(f"\n>>> {title}\n{body}\n")
    if os.environ.get("CI") != "true" and sys.platform == "darwin":
        notify_macos(title, body.split("\n", 1)[0])
    notify_telegram(body)
    notify_email(title, body)


def load_notified_state(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("notified", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_notified_state(path: Path, notified: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"notified": sorted(notified)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_check(notified: set[str], *, state_file: Path) -> set[str]:
    now = datetime.now(TZ).strftime("%d.%m.%Y %H:%M:%S")

    if use_staronki():
        client = StaronkiClient(state_file.parent / "staronki_cookies.txt")
        try:
            status = client.availability()
        finally:
            client.save()
        backend = "staronki.by"
    else:
        html = fetch_route_html()
        status = parse_availability(html)
        backend = "pass.rw.by"

    line = " | ".join(
        f"{train}: {'ЕСТЬ МЕСТА' if info['available'] else 'мест нет'}"
        for train, info in status.items()
    )
    print(f"[{now}] ({backend}) {line}")
    for train in TRAINS:
        log = status[train].get("log")
        if log:
            print(f"  {train}: {log}")

    for train, info in status.items():
        if info["available"] and train not in notified:
            body = (
                f"Появились билеты!\n"
                f"Поезд {train}\n"
                f"{FROM_STATION} → {TO_STATION}\n"
                f"Дата: {DATE}\n\n"
                f"Купить: {buy_link(train)}"
            )
            notify_all(f"Билет БЖД {train}", body)
            notified.add(train)
    return notified


def run_once(state_file: Path) -> int:
    if datetime.now(TZ) >= STOP_AFTER:
        print("Мониторинг завершён: дата поездки прошла.")
        return 0

    notified = load_notified_state(state_file)
    try:
        notified = run_check(notified, state_file=state_file)
        save_notified_state(state_file, notified)
    except Exception as exc:  # noqa: BLE001
        print(f"Ошибка проверки: {exc}", file=sys.stderr)
        # Не падаем в CI из-за временных сбоев / блокировки IP
        return 0

    if len(notified) == len(TRAINS):
        print("Оба поезда уже с местами — уведомления отправлены.")
    return 0


def run_loop(state_file: Path) -> int:
    print(
        f"Мониторинг БЖД: {FROM_STATION} → {TO_STATION}, {DATE}\n"
        f"Поезда: {', '.join(TRAINS)}\n"
        f"Интервал: {CHECK_INTERVAL_SEC} сек.\n"
        f"Остановка: {STOP_AFTER.strftime('%d.%m.%Y %H:%M')} (Минск)\n"
    )

    notified = load_notified_state(state_file)

    while datetime.now(TZ) < STOP_AFTER:
        try:
            notified = run_check(notified, state_file=state_file)
            save_notified_state(state_file, notified)
        except Exception as exc:  # noqa: BLE001
            now = datetime.now(TZ).strftime("%d.%m.%Y %H:%M:%S")
            print(f"[{now}] Ошибка проверки: {exc}", file=sys.stderr)

        if len(notified) == len(TRAINS):
            print("Оба поезда с местами — мониторинг завершён.")
            return 0

        time.sleep(CHECK_INTERVAL_SEC)

    print("Время вышло — мониторинг остановлен.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Монитор билетов БЖД")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Одна проверка (для GitHub Actions)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    load_env_file(script_dir / "config.env")

    state_file = Path(
        os.environ.get("STATE_FILE", script_dir / ".cache/notified.json")
    )

    if args.once:
        return run_once(state_file)
    return run_loop(state_file)


if __name__ == "__main__":
    raise SystemExit(main())
