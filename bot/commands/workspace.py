"""
workspace.py — /guide command for cross-project guidance.

Writes user guidance into /Users/yash/ClaudeWorkspace/_workspace-os/inbox/pending.jsonl.
Claude (in any sibling project) reads this inbox at session start via the
cross-project-memory skill and applies the guidance.

This is the "user → claude" channel of the cross-project bridge.
The reverse channel (claude → user) is _workspace-os/bin/notify, which
sends a Telegram message and writes a "question" entry to the same inbox.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import get_logger

logger = get_logger(__name__)

INBOX = Path("/Users/yash/ClaudeWorkspace/_workspace-os/inbox/pending.jsonl")

# Known sibling projects — used for fuzzy matching when the user types a partial name.
KNOWN_PROJECTS = {
    "jobs-os", "jobsos", "jobs",
    "mmt-os", "mmtos", "mmt", "prism",
    "yos",
    "portfolio",
    "gmailorganization", "gmail",
    "all",
    "_workspace-os", "workspace",
}


def _normalize_project(raw: str) -> str:
    """Map fuzzy input to canonical project name. Falls back to lowercase raw."""
    lo = raw.lower()
    aliases = {
        "jobsos": "jobs-os",
        "jobs": "jobs-os",
        "mmtos": "mmt-os",
        "mmt": "mmt-os",
        "prism": "mmt-os",
        "gmail": "gmailorganization",
        "workspace": "_workspace-os",
    }
    return aliases.get(lo, lo)


async def cmd_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/guide <project> <message> — push guidance to a workspace project's inbox.

    Examples:
      /guide jobs-os port groq, classifier-only
      /guide all enable verbose logging on every classifier run
      /guide mmt-os skip the lenses fix until next week
    """
    args = context.args or []
    if len(args) < 2:
        projects_hint = ", ".join(sorted(p for p in KNOWN_PROJECTS if not p.startswith("_") and p != "all"))
        await update.message.reply_text(
            "Usage: `/guide <project> <message>`\n\n"
            "Examples:\n"
            "  `/guide jobs-os port groq, classifier-only`\n"
            "  `/guide mmt-os skip lenses fix this week`\n"
            "  `/guide all add a daily digest`\n\n"
            f"Known projects: {projects_hint}, all",
            parse_mode="Markdown",
        )
        return

    project = _normalize_project(args[0])
    message = " ".join(args[1:]).strip()

    INBOX.parent.mkdir(parents=True, exist_ok=True)

    # If the message starts with "re:" or "answer:" or matches a recent question id pattern,
    # treat as an answer and try to mark the matching question as answered.
    answered_id = None
    answer_marker = None
    lowered = message.lower()
    for prefix in ("answer:", "re:", "->", "→"):
        if lowered.startswith(prefix):
            answer_marker = prefix
            break

    if answer_marker:
        body = message[len(answer_marker):].strip()
        # Find the most recent unanswered "question" for this project
        try:
            existing = []
            if INBOX.exists():
                for line in INBOX.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            for r in reversed(existing):
                if (
                    r.get("kind") == "question"
                    and r.get("status") == "pending"
                    and r.get("project", "").lower() == project.lower()
                ):
                    answered_id = r.get("id")
                    break
            if answered_id:
                # Rewrite the file with the question marked answered
                lines = []
                for r in existing:
                    if r.get("id") == answered_id:
                        r["status"] = "answered"
                        r["answer"] = body
                        r["answered_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    lines.append(json.dumps(r))
                INBOX.write_text("\n".join(lines) + "\n")
                message = body  # store just the answer body, not the prefix
        except Exception as exc:
            logger.exception(f"failed to match answer: {exc}")

    entry = {
        "id": f"{int(time.time())}-tg",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": "guidance" if not answered_id else "answer",
        "project": project,
        "from": "user",
        "text": message,
        "status": "unread",
    }
    if answered_id:
        entry["answers"] = answered_id

    with INBOX.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    if answered_id:
        await update.message.reply_text(
            f"✅ Answered question `{answered_id}` for *{project}*:\n\n> {message}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"📝 Saved guidance for *{project}*:\n\n> {message}\n\n"
            f"_Claude will pick this up at the next session in that project._",
            parse_mode="Markdown",
        )


async def handle_natural(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Free-text handler: plain messages → real Claude conversation in active project.

    Behavior:
      • Loads the active project's CLAUDE.md + recent commits + open inbox
        questions and feeds them to the active domain agent (lens).
      • Replies are tagged `📂 [<project>] · <emoji> <agent>` at the top so
        the user always knows which project they're talking to.
      • Per-project conversation is preserved across messages; switching
        projects via /project swaps the thread without wiping it.
      • Use /guide for the explicit "save to inbox without LLM" channel.
    """
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text or text.startswith("/"):
        return  # commands handled elsewhere

    # Lazy imports keep this module light and avoid circular deps at startup.
    from store.database import (
        get_agent_state,
        get_project_conversation,
        append_project_message,
    )
    from utils.project_context import load_project_context
    from agents.domain import AGENTS, invoke

    state = get_agent_state()
    project = state.get("active_project") or "jobs-os"
    agent_name = state.get("agent_name") or "product"
    history = get_project_conversation(project)
    project_ctx = load_project_context(project)

    await update.message.chat.send_action("typing")

    try:
        response = invoke(agent_name, text, history, project_context=project_ctx, max_tokens=2048)
    except Exception as exc:
        logger.exception(f"natural-language invoke failed for {project}/{agent_name}: {exc}")
        await update.message.reply_text(
            "⚠️ Couldn't reach Claude. Check ANTHROPIC_API_KEY / network and try again."
        )
        return

    append_project_message(project, "user", text)
    append_project_message(project, "assistant", response)

    mod = AGENTS.get(agent_name)
    emoji = mod.EMOJI if mod else "🤖"
    header = f"📂 *[{project}]* · {emoji} {agent_name}\n\n"

    full = header + response
    if len(full) <= 4000:
        await update.message.reply_text(full, parse_mode="Markdown")
    else:
        # Send the header alone first, then chunk the body.
        await update.message.reply_text(header, parse_mode="Markdown")
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i + 4000])


async def cmd_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/inbox [project] — show pending guidance + open questions across the workspace."""
    project_filter = None
    if context.args:
        project_filter = _normalize_project(context.args[0])

    if not INBOX.exists():
        await update.message.reply_text("📭 Inbox is empty.")
        return

    rows = []
    for line in INBOX.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if project_filter:
        rows = [r for r in rows if r.get("project", "").lower() in (project_filter.lower(), "all")]

    # Show last 10, oldest first
    rows = rows[-10:]
    if not rows:
        await update.message.reply_text("📭 No matching entries.")
        return

    lines = ["*📥 Workspace inbox (last 10)*\n"]
    for r in rows:
        kind = r.get("kind", "?")
        proj = r.get("project", "?")
        text = r.get("text", "")[:120]
        status = r.get("status", "")
        emoji = {"guidance": "📝", "question": "❓", "answer": "✅"}.get(kind, "•")
        lines.append(f"{emoji} *[{proj}]* `{status}` — {text}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
