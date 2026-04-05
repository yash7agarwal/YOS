from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from store.database import init_db
from bot.dispatcher import register
from utils.logger import get_logger

load_dotenv()
logger = get_logger("yos.bot")

YOS_DIR = Path(__file__).parent.parent


def _write_pid() -> None:
    (YOS_DIR / "logs" / "bot.pid").write_text(str(os.getpid()))


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    init_db()
    _write_pid()
    logger.info("YOS database ready.")

    app = ApplicationBuilder().token(token).build()
    register(app)

    logger.info("YOS bot starting — polling…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
