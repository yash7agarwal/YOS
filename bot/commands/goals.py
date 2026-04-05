from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from store.database import add_goal, get_goals, log_checkin, update_goal_progress
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_TIMEFRAMES = {"daily", "weekly", "quarterly", "yearly"}
TIMEFRAME_EMOJI = {"daily": "📅", "weekly": "🗓️", "quarterly": "📊", "yearly": "🎯"}


async def cmd_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/goal <daily|weekly|quarterly|yearly> <title>"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/goal daily|weekly|quarterly|yearly <title>`",
            parse_mode="Markdown",
        )
        return

    timeframe = context.args[0].lower()
    if timeframe not in VALID_TIMEFRAMES:
        await update.message.reply_text(
            f"Timeframe must be one of: {', '.join(VALID_TIMEFRAMES)}"
        )
        return

    title = " ".join(context.args[1:])
    now = datetime.utcnow()
    quarter = f"Q{(now.month - 1) // 3 + 1} {now.year}" if timeframe == "quarterly" else ""

    goal_id = add_goal(title=title, timeframe=timeframe, quarter=quarter)
    emoji = TIMEFRAME_EMOJI[timeframe]
    await update.message.reply_text(
        f"{emoji} Goal #{goal_id} added ({timeframe.upper()})\n`{title}`",
        parse_mode="Markdown",
    )


async def cmd_goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/goals — view all active goals grouped by timeframe"""
    goals = get_goals(status="active")

    if not goals:
        await update.message.reply_text(
            "No active goals. Add one with `/goal daily|weekly|quarterly|yearly <title>`",
            parse_mode="Markdown",
        )
        return

    grouped: dict[str, list] = {}
    for g in goals:
        grouped.setdefault(g["timeframe"], []).append(g)

    lines = ["*Active Goals*\n"]
    for tf in ["daily", "weekly", "quarterly", "yearly"]:
        if tf not in grouped:
            continue
        emoji = TIMEFRAME_EMOJI[tf]
        lines.append(f"{emoji} *{tf.upper()}*")
        for g in grouped[tf]:
            bar = _progress_bar(g["progress"])
            lines.append(f"  `#{g['id']}` {g['title']} {bar}")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip(), parse_mode="Markdown")


async def cmd_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/progress <id> <0-100> — update goal progress"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: `/progress <goal_id> <0-100>`", parse_mode="Markdown")
        return
    try:
        goal_id = int(context.args[0])
        pct = max(0, min(100, int(context.args[1])))
    except ValueError:
        await update.message.reply_text("Both arguments must be numbers.")
        return

    update_goal_progress(goal_id, pct)
    status = "completed" if pct >= 100 else "updated"
    await update.message.reply_text(
        f"{'✅' if pct >= 100 else '📈'} Goal #{goal_id} {status} at {pct}% {_progress_bar(pct)}"
    )


async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/checkin <mood> <notes> — log a daily check-in"""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/checkin <mood: 1-5> <your notes>`\n\nExample: `/checkin 4 Shipped the YOS bot today`",
            parse_mode="Markdown",
        )
        return

    try:
        mood_val = int(args[0])
        mood = str(max(1, min(5, mood_val)))
    except ValueError:
        mood = "3"
        args = ["3"] + list(args)

    notes = " ".join(args[1:]) if len(args) > 1 else ""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    log_checkin(checkin_date=today, checkin_type="daily", notes=notes, mood=mood)

    mood_emoji = ["", "😴", "😐", "🙂", "😊", "🔥"][int(mood)]
    await update.message.reply_text(
        f"✅ Check-in logged for {today}\nMood: {mood_emoji} ({mood}/5)\n_{notes}_" if notes
        else f"✅ Check-in logged for {today}\nMood: {mood_emoji} ({mood}/5)",
        parse_mode="Markdown",
    )


def _progress_bar(pct: int) -> str:
    filled = round(pct / 10)
    return f"[{'█' * filled}{'░' * (10 - filled)}] {pct}%"
