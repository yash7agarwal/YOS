"""Tests for bot/commands/project.py: fuzzy normalization + dispatcher binding."""
from __future__ import annotations

from telegram.ext import Application, CommandHandler

from bot.commands.project import _normalize
from bot.dispatcher import register


def test_normalize_aliases() -> None:
    assert _normalize("jobs") == "jobs-os"
    assert _normalize("jobsos") == "jobs-os"
    assert _normalize("MMT") == "mmt-os"
    assert _normalize("prism") == "mmt-os"
    assert _normalize("workspace") == "_workspace-os"
    assert _normalize("yos") == "yos"
    assert _normalize("UNKNOWN-PROJECT") == "unknown-project"


def test_project_and_p_both_register_to_cmd_project() -> None:
    """/project and /p must both resolve to bot.commands.project.cmd_project."""
    app = Application.builder().token("123:dummy-token-for-tests").build()
    register(app)

    project_handlers: list[CommandHandler] = []
    for group in app.handlers.values():
        for h in group:
            if isinstance(h, CommandHandler) and h.commands & {"project", "p"}:
                project_handlers.append(h)

    assert len(project_handlers) == 2, (
        f"Expected 2 handlers (/project, /p), got {len(project_handlers)}: "
        f"{[sorted(h.commands) for h in project_handlers]}"
    )
    for h in project_handlers:
        cb = h.callback
        assert cb.__module__ == "bot.commands.project", (
            f"Handler for {sorted(h.commands)} routes to {cb.__module__}, expected bot.commands.project"
        )
        assert cb.__name__ == "cmd_project"
