from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from store.database import add_journal_entry, get_journal_entries
from utils.logger import get_logger

logger = get_logger(__name__)

CATEGORY_EMOJIS = {
    "moment": "💭",
    "win": "🏆",
    "learning": "📚",
    "idea": "💡",
    "reflection": "🔍",
}


async def cmd_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/note <text> — capture a moment or thought"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: `/note <your thought>`\n\nTip: prefix with a category:\n`/note win: Shipped X today`\n`/note learning: Learned Y`",
            parse_mode="Markdown",
        )
        return

    # Auto-detect category from prefix
    category = "moment"
    for cat in CATEGORY_EMOJIS:
        if text.lower().startswith(f"{cat}:") or text.lower().startswith(f"{cat} "):
            category = cat
            break

    entry_id = add_journal_entry(content=text, category=category)
    emoji = CATEGORY_EMOJIS.get(category, "💭")
    await update.message.reply_text(
        f"{emoji} Noted! *(#{entry_id})*\n`{text}`",
        parse_mode="Markdown",
    )


async def cmd_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/journal — show recent journal entries"""
    try:
        days = int(context.args[0]) if context.args else 3
    except ValueError:
        days = 3

    entries = get_journal_entries(days=days)
    if not entries:
        await update.message.reply_text(
            f"No journal entries in the last {days} days.\nUse `/note <text>` to add one.",
            parse_mode="Markdown",
        )
        return

    lines = [f"*Journal — last {days} days* ({len(entries)} entries)\n"]
    current_date = None
    for e in entries:
        date = e["entry_date"]
        if date != current_date:
            lines.append(f"*{date}*")
            current_date = date
        emoji = CATEGORY_EMOJIS.get(e["category"], "💭")
        lines.append(f"{emoji} {e['content']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
