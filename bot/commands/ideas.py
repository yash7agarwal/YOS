from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from store.database import add_idea, get_backlog, get_idea, update_idea_priority, update_idea_status
from utils.claude_client import ask_fast
from utils.logger import get_logger

logger = get_logger(__name__)

STATUS_EMOJIS = {"inbox": "📥", "in_progress": "🔄", "done": "✅", "archived": "📦"}


async def cmd_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture an idea: /idea <text>"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: `/idea <your idea>`", parse_mode="Markdown")
        return

    idea_id = add_idea(title=text, source="telegram")
    await update.message.reply_text(
        f"💡 Idea #{idea_id} captured!\n`{text}`\n\nUse `/prioritize {idea_id}` to score it.",
        parse_mode="Markdown",
    )


async def cmd_backlog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/backlog — show top 10 inbox ideas"""
    status = context.args[0] if context.args else "inbox"
    items = get_backlog(status=status, limit=10)

    if not items:
        await update.message.reply_text(f"No ideas in `{status}`. Use `/idea <text>` to add one.", parse_mode="Markdown")
        return

    lines = [f"*Backlog — {status.upper()}* ({len(items)} items)\n"]
    for i in items:
        score = f" [{i['priority_score']:.1f}]" if i["priority_score"] else ""
        emoji = STATUS_EMOJIS.get(i["status"], "•")
        lines.append(f"{emoji} `#{i['id']}` {i['title']}{score}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_prioritize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/prioritize <id> — score an idea with Claude"""
    if not context.args:
        await update.message.reply_text("Usage: `/prioritize <idea_id>`", parse_mode="Markdown")
        return

    try:
        idea_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Idea ID must be a number.")
        return

    idea = get_idea(idea_id)
    if not idea:
        await update.message.reply_text(f"Idea #{idea_id} not found.")
        return

    await update.message.reply_text(f"Scoring idea #{idea_id}…")

    prompt = f"""Score this product/project idea from 0.0 to 10.0 based on:
- Impact potential
- Feasibility
- Alignment with an AI-focused product builder's career

Idea: {idea['title']}
Description: {idea.get('description', '')}

Respond ONLY as JSON: {{"score": 7.5, "reason": "one sentence"}}"""

    raw = ask_fast(prompt, max_tokens=100)
    import json
    try:
        result = json.loads(raw.strip())
        score = float(result["score"])
        reason = result["reason"]
    except Exception:
        score, reason = 5.0, "Could not parse Claude response"

    update_idea_priority(idea_id, score, reason)
    await update.message.reply_text(
        f"*Idea #{idea_id}* scored *{score}/10*\n_{reason}_",
        parse_mode="Markdown",
    )


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/done <id> — mark idea as done"""
    if not context.args:
        await update.message.reply_text("Usage: `/done <idea_id>`", parse_mode="Markdown")
        return
    try:
        idea_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Idea ID must be a number.")
        return
    update_idea_status(idea_id, "done")
    await update.message.reply_text(f"✅ Idea #{idea_id} marked as done.")
