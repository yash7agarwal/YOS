from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from store.database import get_briefing, get_latest_agent_summaries
from utils.logger import get_logger

logger = get_logger(__name__)

AGENT_DISPLAY = {
    "tech_intel": ("💻", "Tech & AI"),
    "biz_intel": ("📊", "Business & Markets"),
    "geo_intel": ("🌍", "Geopolitics"),
}


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/brief — get today's full intelligence briefing (generate if needed)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    briefing = get_briefing(today)

    if not briefing:
        await update.message.reply_text("No briefing yet for today. Generating now…")
        try:
            from intelligence.briefing import compose_briefing
            briefing = compose_briefing(today)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not generate briefing: {e}")
            return

    # Telegram message limit is 4096 chars; split if needed
    if len(briefing) <= 4000:
        await update.message.reply_text(briefing, parse_mode="Markdown")
    else:
        for chunk in _split(briefing, 4000):
            await update.message.reply_text(chunk, parse_mode="Markdown")


async def cmd_tech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/tech — latest tech & AI signals"""
    await _send_agent_summary(update, "tech_intel")


async def cmd_biz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/biz — business & markets snapshot"""
    await _send_agent_summary(update, "biz_intel")


async def cmd_geo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/geo — geopolitics briefing"""
    await _send_agent_summary(update, "geo_intel")


async def cmd_run_agents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/run — manually trigger all agents + compose briefing"""
    await update.message.reply_text("⚙️ Running intelligence agents… this takes ~30s.")
    try:
        from scheduler.daily import run_daily
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_daily)
        await update.message.reply_text("✅ Done. Use `/brief` to see today's briefing.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")


async def _send_agent_summary(update: Update, agent: str) -> None:
    summaries = get_latest_agent_summaries()
    emoji, label = AGENT_DISPLAY.get(agent, ("🔍", agent))
    summary = summaries.get(agent)

    if not summary:
        await update.message.reply_text(
            f"{emoji} No {label} data yet. Use `/run` to fetch today's intel.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"{emoji} *{label}*\n\n{summary}",
        parse_mode="Markdown",
    )


def _split(text: str, max_len: int) -> list[str]:
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks
