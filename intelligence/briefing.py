from __future__ import annotations

from datetime import datetime

from store.database import (
    get_briefing, get_latest_agent_summaries, save_briefing, mark_briefing_sent,
    days_since_health_log, get_jobs,
)
from integrations.gmail import get_briefing_snippet
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

    # Career: top job match
    top_jobs = get_jobs(status="new", min_score=0.0)
    if top_jobs:
        top = top_jobs[0]
        score_pct = int(top["match_score"] * 100)
        lines += [
            "", SECTION_DIVIDER, "",
            "🎯 *Top Career Match*",
            f"• *{top['title']}* @ {top.get('company', '?')} — {score_pct}% match",
            f"  _{top.get('match_reason', '')}_",
        ]

    # Phase 4: Health gap alert
    health_days = days_since_health_log()
    if health_days >= 1:
        lines += [
            "", SECTION_DIVIDER, "",
            f"⚠️ *Health Check* — No log in {health_days} day(s). Use `/health` to log today.",
        ]

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
