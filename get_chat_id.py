#!/usr/bin/env python3
"""После /start в @mytrain34636_bot запустите: python3 get_chat_id.py"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


def load_token() -> str:
    env = Path(__file__).parent / "config.env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    raise SystemExit("Нет TELEGRAM_BOT_TOKEN в config.env")


def main() -> None:
    token = load_token()
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.load(resp)

    updates = data.get("result", [])
    if not updates:
        print("Пока пусто. Откройте t.me/mytrain34636_bot → Start → напишите «привет»")
        print("Потом снова: python3 get_chat_id.py")
        return

    last = updates[-1]
    chat = last.get("message", {}).get("chat") or last.get("callback_query", {}).get("message", {}).get("chat")
    if not chat:
        print("Сообщений нет. Напишите боту /start")
        return

    chat_id = chat["id"]
    print(f"TELEGRAM_CHAT_ID={chat_id}")
    print()
    print("Дальше:")
    print(f'  echo "TELEGRAM_CHAT_ID={chat_id}" >> config.env')
    print(f'  gh secret set TELEGRAM_CHAT_ID --body "{chat_id}"')


if __name__ == "__main__":
    main()
