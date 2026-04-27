"""
project_context.py — load context for a sibling workspace project.

Used by the Telegram bot's natural-language handler so plain-text messages
get answered with full awareness of the active project (CLAUDE.md, recent
commits, recent inbox questions). Cached in-memory for 5 minutes per project.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

WORKSPACE_ROOT = Path("/Users/yash/ClaudeWorkspace")
INBOX = WORKSPACE_ROOT / "_workspace-os" / "inbox" / "pending.jsonl"

PROJECT_PATHS: dict[str, Path] = {
    "jobs-os":           WORKSPACE_ROOT / "Jobs-OS",
    "mmt-os":            WORKSPACE_ROOT / "MMT-OS",
    "yos":               WORKSPACE_ROOT / "YOS",
    "portfolio":         WORKSPACE_ROOT / "portfolio",
    "gmailorganization": WORKSPACE_ROOT / "GmailOrganization",
    "_workspace-os":     WORKSPACE_ROOT / "_workspace-os",
}

# Per-project context budgets (chars, ~4 chars/token).
CLAUDE_MD_BUDGET = 6000
LEARNINGS_BUDGET = 2000

_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL_SECONDS = 300


def known_projects() -> list[str]:
    return sorted(PROJECT_PATHS.keys())


def project_path(project: str) -> Path | None:
    return PROJECT_PATHS.get(project.lower())


def _read_truncated(path: Path, budget: int) -> str:
    try:
        text = path.read_text()
    except (FileNotFoundError, PermissionError):
        return ""
    if len(text) <= budget:
        return text
    head = text[: budget - 200]
    tail = text[-200:]
    return f"{head}\n\n…[truncated for context budget]…\n\n{tail}"


def _recent_commits(repo: Path, n: int = 3) -> str:
    try:
        out = subprocess.run(
            ["git", "log", f"-n{n}", "--pretty=format:%h %s (%cr)"],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return ""


def _open_questions(project: str, n: int = 3) -> list[dict]:
    """Return the most recent unanswered 'question' entries for this project."""
    if not INBOX.exists():
        return []
    rows: list[dict] = []
    try:
        for line in INBOX.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    matched: list[dict] = []
    for r in reversed(rows):
        if (
            r.get("kind") == "question"
            and r.get("status") == "pending"
            and r.get("project", "").lower() == project.lower()
        ):
            matched.append(r)
            if len(matched) >= n:
                break
    return matched


def _build(project: str) -> str:
    project = project.lower()
    path = project_path(project)
    if path is None or not path.exists():
        return f"⚠️  Project `{project}` not found on disk; no context loaded."

    parts: list[str] = [f"# Active project: {project}", f"# Path: {path}"]

    claude_md = _read_truncated(path / "CLAUDE.md", CLAUDE_MD_BUDGET)
    if claude_md:
        parts.append("\n## Project CLAUDE.md (instructions for Claude in this repo)\n")
        parts.append(claude_md)

    learnings = _read_truncated(path / "memory" / "learnings.md", LEARNINGS_BUDGET)
    if learnings:
        parts.append("\n## Project learnings (memory/learnings.md)\n")
        parts.append(learnings)

    commits = _recent_commits(path)
    if commits:
        parts.append("\n## Recent commits\n")
        parts.append(commits)

    questions = _open_questions(project)
    if questions:
        parts.append("\n## Open questions Claude has asked the user (in this project)\n")
        for q in questions:
            qid = q.get("id", "?")
            qtext = q.get("text", "")[:400]
            parts.append(f"- [{qid}] {qtext}")
        parts.append(
            "\n_If the user's message answers one of these, name the question id "
            "in your reply so they can mark it answered with `/guide " + project + " answer: <text>`._"
        )

    return "\n".join(parts)


def load_project_context(project: str) -> str:
    """Return the system-prompt-ready context block for a project. Cached 5 min."""
    project = project.lower()
    now = time.time()
    cached = _cache.get(project)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]
    try:
        ctx = _build(project)
    except Exception as exc:
        logger.exception(f"failed to build context for {project}: {exc}")
        ctx = f"⚠️  Failed to load context for `{project}`."
    _cache[project] = (now, ctx)
    return ctx


def invalidate_cache(project: str | None = None) -> None:
    """Drop cached context — call after switching projects or editing CLAUDE.md."""
    if project is None:
        _cache.clear()
    else:
        _cache.pop(project.lower(), None)
