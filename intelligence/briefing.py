from __future__ import annotations

from datetime import datetime

from store.database import get_briefing, get_latest_agent_summaries, save_briefing, mark_briefing_sent
from integrations.gmail import get_briefing_snippet
from utils.claude_client import ask
from utils.telegram import send_message
from utils.logger import get_logger

logger = get_logger(__name__)

SECTION_DIVIDER = "━" * 28


def compose_briefing(date: str | None = None) -> str:
    """
    Compose the daily briefing from latest agent summaries + Gmail insights.
    Saves to the briefings table. Returns the full text.
    """
    date = date or datetime.utcnow().strftime("%Y-%m-%d")

    # Check if already composed today
    existing = get_briefing(date)
    if existing:
        logger.info(f"Briefing for {date} already exists, returning cached.")
        return existing

    summaries = get_latest_agent_summaries()
    tech = summaries.get("tech_intel", "_No tech data today_")
    biz = summaries.get("biz_intel", "_No business data today_")
    geo = summaries.get("geo_intel", "_No geo data today_")
    gmail_snippet = get_briefing_snippet()

    # Format date nicely
    dt = datetime.strptime(date, "%Y-%m-%d")
    display_date = dt.strftime("%b %-d, %Y")

    lines = [
        f"🧠 *YOS Briefing — {display_date}*",
        SECTION_DIVIDER,
        "",
        "💻 *Tech & AI*",
        tech,
        "",
        "📊 *Business & Markets*",
        biz,
        "",
        "🌍 *Geopolitics*",
        geo,
    ]

    if gmail_snippet:
        lines += ["", SECTION_DIVIDER, "", gmail_snippet]

    briefing_text = "\n".join(lines)

    save_briefing(date, briefing_text)
    logger.info(f"Briefing composed and saved for {date} ({len(briefing_text)} chars)")
    return briefing_text


def send_briefing(date: str | None = None) -> bool:
    """Send today's briefing via Telegram. Returns True on success."""
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    text = compose_briefing(date)
    ok = send_message(text)
    if ok:
        mark_briefing_sent(date)
        logger.info(f"Briefing for {date} sent via Telegram.")
    else:
        logger.error(f"Failed to send briefing for {date}.")
    return ok
