from __future__ import annotations

import os
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from store.database import init_db
from utils.logger import get_logger

load_dotenv()
logger = get_logger("yos.scheduler")

YOS_DIR = Path(__file__).parent.parent
DAILY_HOUR   = int(os.getenv("DAILY_HOUR",   "7"))
DAILY_MINUTE = int(os.getenv("DAILY_MINUTE", "0"))


def _write_pid() -> None:
    (YOS_DIR / "logs" / "scheduler.pid").write_text(str(os.getpid()))


def main() -> None:
    init_db()
    _write_pid()

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # ── Daily: pipeline agents + briefing (07:00 IST) ───────────────────────
    scheduler.add_job(
        _run_daily,
        CronTrigger(hour=DAILY_HOUR, minute=DAILY_MINUTE),
        id="daily_briefing",
        name="Daily intelligence briefing",
        misfire_grace_time=600,
    )

    # ── Weekly: deep research + backlog curation (Monday 08:00 IST) ─────────
    scheduler.add_job(
        _run_weekly,
        CronTrigger(day_of_week="mon", hour=8, minute=15),
        id="weekly_research",
        name="Weekly deep research + backlog curator",
        misfire_grace_time=1800,
    )

    # ── Monthly: OS report (1st of month, 09:00 IST) ────────────────────────
    scheduler.add_job(
        _run_monthly,
        CronTrigger(day=1, hour=9, minute=0),
        id="monthly_report",
        name="Monthly OS report",
        misfire_grace_time=3600,
    )

    # ── System health check (every 6 hours) ─────────────────────────────────
    scheduler.add_job(
        _run_health_check,
        CronTrigger(hour="*/6", minute=7),
        id="system_health",
        name="System health check + auto-restart",
        misfire_grace_time=300,
    )

    logger.info(f"Scheduler started:")
    logger.info(f"  Daily    → {DAILY_HOUR:02d}:{DAILY_MINUTE:02d} IST")
    logger.info(f"  Weekly   → Monday 08:15 IST")
    logger.info(f"  Monthly  → 1st of month 09:00 IST")
    logger.info(f"  Health   → every 6h")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def _run_daily() -> None:
    from scheduler.daily import run_daily
    run_daily()


def _run_weekly() -> None:
    from scheduler.weekly import run_weekly
    run_weekly()


def _run_monthly() -> None:
    from scheduler.monthly import run_monthly
    run_monthly()


def _run_health_check() -> None:
    from agents.claude.system_health import run
    run()


if __name__ == "__main__":
    if "--now" in sys.argv:
        logger.info("Running daily pipeline immediately.")
        from scheduler.daily import run_daily
        run_daily()
    elif "--weekly" in sys.argv:
        logger.info("Running weekly pipeline immediately.")
        from scheduler.weekly import run_weekly
        run_weekly()
    elif "--monthly" in sys.argv:
        logger.info("Running monthly pipeline immediately.")
        from scheduler.monthly import run_monthly
        run_monthly()
    elif "--health" in sys.argv:
        logger.info("Running health check immediately.")
        from agents.claude.system_health import run
        run()
    else:
        main()
