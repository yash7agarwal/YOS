from __future__ import annotations

import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from store.database import init_db
from utils.logger import get_logger

load_dotenv()
logger = get_logger("yos.scheduler")

# Daily briefing time — default 07:00 local
DAILY_HOUR = int(os.getenv("DAILY_HOUR", "7"))
DAILY_MINUTE = int(os.getenv("DAILY_MINUTE", "0"))


def main() -> None:
    init_db()

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # Daily intelligence briefing
    scheduler.add_job(
        _run_daily,
        CronTrigger(hour=DAILY_HOUR, minute=DAILY_MINUTE),
        id="daily_briefing",
        name="Daily intelligence briefing",
        misfire_grace_time=600,
    )

    logger.info(f"Scheduler started — daily briefing at {DAILY_HOUR:02d}:{DAILY_MINUTE:02d} IST")
    logger.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def _run_daily() -> None:
    from scheduler.daily import run_daily
    run_daily()


if __name__ == "__main__":
    # Allow running manually: python -m scheduler.main --now
    if "--now" in sys.argv:
        logger.info("Running daily pipeline immediately (--now flag).")
        from scheduler.daily import run_daily
        run_daily()
    else:
        main()
