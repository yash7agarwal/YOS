from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from store.database import (
    get_jobs, update_job_status,
    get_skills, add_skill,
    get_latest_resume, save_resume_version,
)
from utils.logger import get_logger

logger = get_logger(__name__)

LEVEL_EMOJI = {"learning": "🌱", "proficient": "💪", "expert": "⭐"}


async def cmd_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/jobs — top job matches"""
    jobs = get_jobs(status="new", min_score=0.0)

    if not jobs:
        await update.message.reply_text(
            "No job matches yet. Use `/run` to trigger the career scanner.",
            parse_mode="Markdown",
        )
        return

    lines = [f"*Top Job Matches* ({len(jobs)} found)\n"]
    for j in jobs[:8]:
        score_pct = int(j["match_score"] * 100)
        bar = "█" * round(score_pct / 20) + "░" * (5 - round(score_pct / 20))
        url_line = f"\n  {j['url']}" if j.get("url") else ""
        lines.append(
            f"`#{j['id']}` *{j['title']}*\n"
            f"  {j.get('company', '?')} [{bar}] {score_pct}%\n"
            f"  _{j.get('match_reason', '')}_" + url_line
        )

    lines.append("\n`/apply <id>` to mark as applied")
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def cmd_apply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/apply <id> — mark a job as applied"""
    if not context.args:
        await update.message.reply_text("Usage: `/apply <job_id>`", parse_mode="Markdown")
        return
    try:
        job_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Job ID must be a number.")
        return
    update_job_status(job_id, "applied")
    await update.message.reply_text(f"✅ Job #{job_id} marked as applied.")


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skills — show full skill map"""
    skills = get_skills()

    if not skills:
        await update.message.reply_text(
            "No skills tracked yet. Use `/skill <name> [level]` to add one.",
            parse_mode="Markdown",
        )
        return

    grouped: dict[str, list] = {}
    for s in skills:
        grouped.setdefault(s["category"] or "General", []).append(s)

    lines = ["*Skill Map*\n"]
    for cat, items in grouped.items():
        lines.append(f"*{cat}*")
        for s in items:
            emoji = LEVEL_EMOJI.get(s["level"], "•")
            lines.append(f"  {emoji} {s['name']} _{s['level']}_")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip(), parse_mode="Markdown")


async def cmd_skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skill <name> [learning|proficient|expert] — add or update a skill"""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/skill <name> [learning|proficient|expert]`\nExample: `/skill Python expert`",
            parse_mode="Markdown",
        )
        return

    valid_levels = {"learning", "proficient", "expert"}
    args = context.args

    if len(args) >= 2 and args[-1].lower() in valid_levels:
        level = args[-1].lower()
        name = " ".join(args[:-1])
    else:
        level = "learning"
        name = " ".join(args)

    # Auto-detect category
    category = _guess_category(name)
    add_skill(name=name, category=category, level=level)
    emoji = LEVEL_EMOJI.get(level, "•")
    await update.message.reply_text(
        f"{emoji} Skill added: *{name}* ({level}) under _{category}_",
        parse_mode="Markdown",
    )


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/resume — show latest or /resume <text> to update"""
    args_text = " ".join(context.args) if context.args else ""

    if args_text:
        # Store new resume version
        version = save_resume_version(content=args_text, change_log="Updated via Telegram")
        await update.message.reply_text(
            f"✅ Resume v{version} saved ({len(args_text)} chars).",
            parse_mode="Markdown",
        )
        return

    # Show current resume
    resume = get_latest_resume()
    if not resume:
        await update.message.reply_text(
            "No resume stored yet.\nUse `/resume <your resume text>` to save one.",
            parse_mode="Markdown",
        )
        return

    content = resume["content"]
    preview = content[:800] + ("…" if len(content) > 800 else "")
    await update.message.reply_text(
        f"*Resume v{resume['version']}*\n\n{preview}",
        parse_mode="Markdown",
    )


def _guess_category(skill_name: str) -> str:
    name = skill_name.lower()
    if any(k in name for k in ["python", "javascript", "typescript", "sql", "react", "node", "go", "rust", "java"]):
        return "Engineering"
    if any(k in name for k in ["llm", "claude", "gpt", "ml", "ai", "agent", "rag", "fine-tun", "embedding"]):
        return "AI/ML"
    if any(k in name for k in ["product", "roadmap", "okr", "jira", "figma", "ux", "user research", "analytics"]):
        return "Product"
    if any(k in name for k in ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd"]):
        return "Infrastructure"
    return "General"
