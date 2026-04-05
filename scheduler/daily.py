from __future__ import annotations

from utils.logger import get_logger

logger = get_logger("yos.scheduler.daily")


def run_daily() -> None:
    """
    Full daily pipeline:
      1. Run all intelligence agents
      2. Compose briefing from summaries + Gmail
      3. Send briefing via Telegram
    """
    logger.info("=== Daily pipeline starting ===")

    # Import here to avoid circular imports at module load
    from agents import tech_intel, biz_intel, geo_intel
    from intelligence.briefing import send_briefing
    from store.database import days_since_health_log
    from utils.telegram import send_message

    # Step 1: Run agents
    logger.info("Running tech_intel agent…")
    tech_intel.run()

    logger.info("Running biz_intel agent…")
    biz_intel.run()

    logger.info("Running geo_intel agent…")
    geo_intel.run()

    # Step 2+3: Compose + send briefing
    logger.info("Composing and sending briefing…")
    ok = send_briefing()

    # Health nudge if needed
    since = days_since_health_log()
    if since >= 1:
        send_message(f"⚠️ No health log in {since} day(s). Use `/health` to log today.")

    logger.info(f"=== Daily pipeline complete. Briefing sent: {ok} ===")
