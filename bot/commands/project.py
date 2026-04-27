"""
project.py — /project command for switching the active workspace project.

Plain-text Telegram messages are routed to the active project's Claude
conversation (with that project's CLAUDE.md + recent context loaded).
This command lets the user see / switch which project is active.
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from store.database import (
    get_agent_state,
    set_active_project,
    get_project_conversation,
    clear_project_conversation,
)
from utils.project_context import known_projects, project_path, invalidate_cache
from utils.logger import get_logger

logger = get_logger(__name__)


def _normalize(raw: str) -> str:
    """Map fuzzy input to canonical project name."""
    aliases = {
        "jobs":      "jobs-os",
        "jobsos":    "jobs-os",
        "mmt":       "mmt-os",
        "mmtos":     "mmt-os",
        "prism":     "mmt-os",
        "gmail":     "gmailorganization",
        "workspace": "_workspace-os",
    }
    lo = raw.lower().strip()
    return aliases.get(lo, lo)


async def cmd_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/project — show active project. /project <name> — switch.

    Examples:
      /project              → show current + list
      /project jobs-os      → switch to jobs-os
      /project mmt-os reset → switch and clear that project's thread
    """
    args = context.args or []
    state = get_agent_state()
    current = state.get("active_project", "jobs-os")

    if not args:
        thread_len = len(get_project_conversation(current))
        path = project_path(current)
        path_line = f"`{path}`" if path else "_(no path on disk)_"
        listing = "\n".join(f"  • `{p}`" for p in known_projects())
        await update.message.reply_text(
            f"📂 *Active project: {current}*\n"
            f"_{thread_len} message{'s' if thread_len != 1 else ''} in thread · {path_line}_\n\n"
            f"*Known projects:*\n{listing}\n\n"
            f"Switch with `/project <name>` · "
            f"Reset thread with `/project {current} reset`",
            parse_mode="Markdown",
        )
        return

    name = _normalize(args[0])
    reset = len(args) > 1 and args[1].lower() in ("reset", "clear", "fresh")

    if project_path(name) is None:
        listing = ", ".join(f"`{p}`" for p in known_projects())
        await update.message.reply_text(
            f"Unknown project `{name}`.\nKnown: {listing}",
            parse_mode="Markdown",
        )
        return

    set_active_project(name)
    invalidate_cache(name)

    if reset:
        clear_project_conversation(name)
        await update.message.reply_text(
            f"📂 *Switched to {name}* — thread cleared. Send any message to start.",
            parse_mode="Markdown",
        )
    else:
        thread_len = len(get_project_conversation(name))
        await update.message.reply_text(
            f"📂 *Switched to {name}*\n"
            f"_{thread_len} message{'s' if thread_len != 1 else ''} in existing thread._\n\n"
            f"Plain text now goes to this project. Use `/project {name} reset` to start fresh.",
            parse_mode="Markdown",
        )
    logger.info(f"[project] switched to {name} (reset={reset})")
