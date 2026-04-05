from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from store.database import get_goals, get_briefing, get_journal_entries, days_since_health_log
from utils.logger import get_logger

logger = get_logger(__name__)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/today — daily dashboard: goals + briefing + journal"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [f"*YOS Daily Dashboard — {today}*\n{'━' * 28}\n"]

    # Goals: daily + weekly
    goals = get_goals(status="active")
    daily = [g for g in goals if g["timeframe"] == "daily"]
    weekly = [g for g in goals if g["timeframe"] == "weekly"]

    if daily:
        lines.append("📅 *Today's Goals*")
        for g in daily:
            pct = g["progress"]
            bar = "█" * round(pct / 20) + "░" * (5 - round(pct / 20))
            lines.append(f"  `#{g['id']}` {g['title']} [{bar}] {pct}%")
        lines.append("")

    if weekly:
        lines.append("🗓️ *This Week*")
        for g in weekly[:3]:
            lines.append(f"  `#{g['id']}` {g['title']}")
        lines.append("")

    if not daily and not weekly:
        lines.append("_No active goals. Add with `/goal daily <title>`_\n")

    # Briefing excerpt
    briefing = get_briefing(today)
    if briefing:
        excerpt = briefing[:400].strip()
        if len(briefing) > 400:
            excerpt += "…"
        lines.append("🧠 *Today's Briefing*")
        lines.append(excerpt)
        lines.append("\nFull briefing: `/brief`\n")
    else:
        lines.append("🧠 _No briefing yet for today. Run `/brief` to generate._\n")

    # Recent journal
    entries = get_journal_entries(days=1)
    if entries:
        lines.append("💭 *Recent Notes*")
        for e in entries[:3]:
            lines.append(f"  • {e['content'][:80]}")
        lines.append("")

    # Health nudge
    since = days_since_health_log()
    if since >= 1:
        lines.append(f"⚠️ _No health log in {since} day(s). Use `/health` to log._\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
