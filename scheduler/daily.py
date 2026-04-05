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
    from agents import tech_intel, biz_intel, geo_intel, career_scanner
    from intelligence.briefing import send_briefing

    # Step 1: Run all intelligence agents
    logger.info("Running tech_intel agent…")
    tech_intel.run()

    logger.info("Running biz_intel agent…")
    biz_intel.run()

    logger.info("Running geo_intel agent…")
    geo_intel.run()

    logger.info("Running career_scanner agent…")
    career_scanner.run()

    # Step 2+3: Compose + send briefing (includes health alert + top job match)
    logger.info("Composing and sending briefing…")
    ok = send_briefing()

    logger.info(f"=== Daily pipeline complete. Briefing sent: {ok} ===")
