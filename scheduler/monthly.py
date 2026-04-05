from __future__ import annotations

from utils.logger import get_logger

logger = get_logger("yos.scheduler.monthly")


def run_monthly() -> None:
    """Monthly pipeline: comprehensive OS report."""
    logger.info("=== Monthly pipeline starting ===")

    from agents.claude.monthly_reporter import run as monthly_reporter

    logger.info("Running monthly_reporter (Claude agent)…")
    monthly_reporter()

    logger.info("=== Monthly pipeline complete ===")
