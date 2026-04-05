from __future__ import annotations

from utils.logger import get_logger

logger = get_logger("yos.scheduler.weekly")


def run_weekly() -> None:
    """Weekly pipeline: deep research analyst + backlog curator."""
    logger.info("=== Weekly pipeline starting ===")

    from agents.claude.weekly_analyst import run as weekly_analyst
    from agents.claude.backlog_curator import run as backlog_curator

    logger.info("Running weekly_analyst (Claude agent)…")
    weekly_analyst()

    logger.info("Running backlog_curator (Claude agent)…")
    backlog_curator()

    logger.info("=== Weekly pipeline complete ===")
