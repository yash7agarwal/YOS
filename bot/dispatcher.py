from __future__ import annotations

import functools
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from store.database import log_bot_interaction
from utils.logger import get_logger
from bot.commands.ideas import cmd_idea, cmd_backlog, cmd_prioritize, cmd_done
from bot.commands.goals import cmd_goal, cmd_goals, cmd_progress, cmd_checkin
from bot.commands.journal import cmd_note, cmd_journal
from bot.commands.health import cmd_health, cmd_healthlog
from bot.commands.today import cmd_today
from bot.commands.intel import cmd_brief, cmd_tech, cmd_biz, cmd_geo, cmd_run_agents, cmd_weekly, cmd_monthly, cmd_health
from bot.commands.career import cmd_jobs, cmd_apply, cmd_skills, cmd_skill, cmd_resume
from bot.commands.domain import cmd_agent, cmd_ask, cmd_reset_agent

load_dotenv()
logger = get_logger(__name__)

ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def _auth(fn):
    """Only respond to the authorized chat ID."""
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(ALLOWED_CHAT_ID):
            return
        cmd = fn.__name__.replace("cmd_", "/")
        text = (update.message.text or "") if update.message else ""
        try:
            await fn(update, context)
            log_bot_interaction("command", text, cmd, "success", response_sent=True)
        except Exception as exc:
            logger.exception(f"Error in {cmd}: {exc}")
            log_bot_interaction("command", text, cmd, "error", str(exc))
            await update.message.reply_text(f"⚠️ Error: {exc}")
    return wrapper


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_chat.id) != str(ALLOWED_CHAT_ID):
        return
    await update.message.reply_text(
        "*YOS — Personal AI OS*\n\n"
        "📥 *Backlog*\n"
        "`/idea <text>` — capture idea\n"
        "`/backlog` — view inbox\n"
        "`/prioritize <id>` — score with AI\n"
        "`/done <id>` — mark complete\n\n"
        "🎯 *Goals*\n"
        "`/goal daily|weekly|quarterly|yearly <title>`\n"
        "`/goals` — view all active\n"
        "`/progress <id> <0-100>`\n"
        "`/checkin <mood 1-5> [notes]`\n\n"
        "💭 *Journal*\n"
        "`/note <text>` — capture moment\n"
        "`/journal [days]` — recent entries\n\n"
        "🩺 *Health*\n"
        "`/health <sleep> <energy> <stress> [notes]`\n"
        "`/healthlog` — last 7 days\n\n"
        "💼 *Career*\n"
        "`/jobs` — top job matches\n"
        "`/apply <id>` — mark as applied\n"
        "`/skills` — skill map\n"
        "`/skill <name> [level]` — add/update skill\n"
        "`/resume` — show or update resume\n\n"
        "🧠 *Intelligence*\n"
        "`/brief` — full daily briefing\n"
        "`/tech` — tech & AI signals\n"
        "`/biz` — business & markets\n"
        "`/geo` — geopolitics\n"
        "`/run` — trigger agents now\n\n"
        "📋 *Dashboard*\n"
        "`/today` — daily overview\n\n"
        "🤖 *Domain Agents*\n"
        "`/agent` — show active agent\n"
        "`/agent <name>` — switch agent (finance|product|strategy|research|contrarian|creative)\n"
        "`/ask <message>` — query active agent\n"
        "`/reset` — clear conversation history",
        parse_mode="Markdown",
    )


def register(app: Application) -> None:
    """Register all command handlers."""
    wrap = _auth

    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))

    # Ideas / backlog
    app.add_handler(CommandHandler("idea", wrap(cmd_idea)))
    app.add_handler(CommandHandler("backlog", wrap(cmd_backlog)))
    app.add_handler(CommandHandler("prioritize", wrap(cmd_prioritize)))
    app.add_handler(CommandHandler("done", wrap(cmd_done)))

    # Goals
    app.add_handler(CommandHandler("goal", wrap(cmd_goal)))
    app.add_handler(CommandHandler("goals", wrap(cmd_goals)))
    app.add_handler(CommandHandler("progress", wrap(cmd_progress)))
    app.add_handler(CommandHandler("checkin", wrap(cmd_checkin)))

    # Journal
    app.add_handler(CommandHandler("note", wrap(cmd_note)))
    app.add_handler(CommandHandler("journal", wrap(cmd_journal)))

    # Health
    app.add_handler(CommandHandler("health", wrap(cmd_health)))
    app.add_handler(CommandHandler("healthlog", wrap(cmd_healthlog)))

    # Dashboard
    app.add_handler(CommandHandler("today", wrap(cmd_today)))

    # Career
    app.add_handler(CommandHandler("jobs", wrap(cmd_jobs)))
    app.add_handler(CommandHandler("apply", wrap(cmd_apply)))
    app.add_handler(CommandHandler("skills", wrap(cmd_skills)))
    app.add_handler(CommandHandler("skill", wrap(cmd_skill)))
    app.add_handler(CommandHandler("resume", wrap(cmd_resume)))

    # Intelligence
    app.add_handler(CommandHandler("brief", wrap(cmd_brief)))
    app.add_handler(CommandHandler("tech", wrap(cmd_tech)))
    app.add_handler(CommandHandler("biz", wrap(cmd_biz)))
    app.add_handler(CommandHandler("geo", wrap(cmd_geo)))
    app.add_handler(CommandHandler("run", wrap(cmd_run_agents)))
    app.add_handler(CommandHandler("weekly", wrap(cmd_weekly)))
    app.add_handler(CommandHandler("monthly", wrap(cmd_monthly)))
    app.add_handler(CommandHandler("syshealth", wrap(cmd_health)))

    # Domain agents
    app.add_handler(CommandHandler("agent",  wrap(cmd_agent)))
    app.add_handler(CommandHandler("agents", wrap(cmd_agent)))
    app.add_handler(CommandHandler("ask",    wrap(cmd_ask)))
    app.add_handler(CommandHandler("reset",  wrap(cmd_reset_agent)))

    logger.info("All command handlers registered.")
