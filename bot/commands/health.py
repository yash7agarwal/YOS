from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from store.database import add_health_log, get_health_logs, days_since_health_log
from utils.logger import get_logger

logger = get_logger(__name__)


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/health <sleep_hrs> <energy 1-5> <stress 1-5> [notes]
    Example: /health 7 4 2 felt good after morning run
    """
    args = context.args or []

    if not args:
        since = days_since_health_log()
        msg = (
            f"⚠️ No health log in {since} days!\n\n" if since > 0
            else ""
        )
        msg += (
            "Usage: `/health <sleep_hrs> <energy 1-5> <stress 1-5> [notes]`\n"
            "Example: `/health 7.5 4 2 morning run, felt great`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    try:
        sleep = float(args[0]) if len(args) > 0 else None
        energy = int(args[1]) if len(args) > 1 else None
        stress = int(args[2]) if len(args) > 2 else None
        notes = " ".join(args[3:]) if len(args) > 3 else ""
    except ValueError:
        await update.message.reply_text(
            "Couldn't parse that. Usage: `/health <sleep_hrs> <energy 1-5> <stress 1-5> [notes]`",
            parse_mode="Markdown",
        )
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    add_health_log(
        log_date=today,
        sleep_hours=sleep,
        exercise="",
        diet_notes="",
        energy=energy,
        stress=stress,
        notes=notes,
    )

    energy_emoji = ["", "😴", "😪", "😐", "💪", "⚡"][energy] if energy else "?"
    stress_emoji = ["", "😌", "🙂", "😐", "😰", "🔥"][stress] if stress else "?"
    await update.message.reply_text(
        f"🩺 Health logged for {today}\n"
        f"😴 Sleep: *{sleep}h*  |  Energy: {energy_emoji} ({energy}/5)  |  Stress: {stress_emoji} ({stress}/5)"
        + (f"\n_{notes}_" if notes else ""),
        parse_mode="Markdown",
    )


async def cmd_healthlog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/healthlog — show last 7 days health"""
    logs = get_health_logs(days=7)
    if not logs:
        await update.message.reply_text("No health logs yet. Use `/health` to log today.", parse_mode="Markdown")
        return

    lines = ["*Health Log — Last 7 Days*\n"]
    for log in logs:
        e = log.get("energy") or "?"
        s = log.get("stress") or "?"
        sl = log.get("sleep_hours") or "?"
        n = f" — {log['notes']}" if log.get("notes") else ""
        lines.append(f"*{log['log_date']}* | 😴{sl}h | ⚡{e}/5 | 😰{s}/5{n}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
