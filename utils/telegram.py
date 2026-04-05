from __future__ import annotations

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(text: str, chat_id: str = CHAT_ID, parse_mode: str = "Markdown") -> bool:
    """Send a message via Telegram. Returns True on success."""
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        r = httpx.post(
            f"{_BASE}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False
