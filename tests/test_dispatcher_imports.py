"""Regression test for the /health dispatcher import-collision bug.

History: bot/dispatcher.py imported `cmd_health` from BOTH
`bot.commands.health` (sleep/energy logger) and `bot.commands.intel`
(system-health agent). The second import silently shadowed the first,
so /health was dead-routed to the system-health agent and the
sleep/energy logger was unreachable. Fixed in commit f099763 by
renaming `intel.cmd_health` -> `cmd_syshealth`.

This test asserts:

  1. /health resolves to a callback whose underlying function lives in
     `bot.commands.health` (NOT `bot.commands.intel`).
  2. /syshealth resolves to a callback whose underlying function lives
     in `bot.commands.intel`.
  3. No two CommandHandler callbacks share the same (__module__,
     __name__) pair -- a general guard against the same shadow-import
     pattern recurring under any other command name.

The test never opens a network connection: it builds an `Application`
in-process with a dummy token and only inspects the handler table.
"""
from __future__ import annotations

from telegram.ext import Application, CommandHandler

from bot.dispatcher import register


def _build_app() -> Application:
    """Construct an Application and register handlers, no network IO."""
    app = Application.builder().token("123:dummy-token-for-tests").build()
    register(app)
    return app


def _command_handlers(app: Application) -> list[CommandHandler]:
    handlers: list[CommandHandler] = []
    for group_handlers in app.handlers.values():
        for h in group_handlers:
            if isinstance(h, CommandHandler):
                handlers.append(h)
    return handlers


def _find_handler(app: Application, command: str) -> CommandHandler:
    for h in _command_handlers(app):
        if command in h.commands:
            return h
    raise AssertionError(
        f"No CommandHandler registered for /{command}. "
        f"Registered: {sorted(c for h in _command_handlers(app) for c in h.commands)}"
    )


def test_health_command_resolves_to_health_module() -> None:
    """/health must route to bot.commands.health.cmd_health, not the intel
    system-health agent. This is the exact regression that bit us."""
    app = _build_app()
    handler = _find_handler(app, "health")
    cb = handler.callback  # _auth wrapper preserves __module__/__name__ via functools.wraps
    assert cb.__name__ == "cmd_health", (
        f"/health callback __name__ is {cb.__name__!r}, expected 'cmd_health'"
    )
    assert cb.__module__ == "bot.commands.health", (
        f"/health callback __module__ is {cb.__module__!r}, expected "
        f"'bot.commands.health'. If this says 'bot.commands.intel' the "
        f"shadow-import bug has regressed (see commit f099763)."
    )


def test_syshealth_command_resolves_to_intel_module() -> None:
    """/syshealth must route to bot.commands.intel.cmd_syshealth."""
    app = _build_app()
    handler = _find_handler(app, "syshealth")
    cb = handler.callback
    assert cb.__name__ == "cmd_syshealth", (
        f"/syshealth callback __name__ is {cb.__name__!r}, expected 'cmd_syshealth'"
    )
    assert cb.__module__ == "bot.commands.intel", (
        f"/syshealth callback __module__ is {cb.__module__!r}, expected 'bot.commands.intel'"
    )


def test_no_duplicate_command_callbacks() -> None:
    """General guard: two CommandHandlers must never share the same
    (__module__, __name__). That signature would mean the same function
    was imported under two names -- the exact symptom of the original
    bug. Aliases that intentionally point at the same function (e.g.
    /agent and /agents both calling cmd_agent) are allowed."""
    app = _build_app()
    seen: dict[tuple[str, str], frozenset[str]] = {}
    duplicates: list[str] = []

    for handler in _command_handlers(app):
        cb = handler.callback
        key = (cb.__module__, cb.__name__)
        if key in seen:
            # Allow the same callable registered under multiple command
            # names (intentional aliases like /agent + /agents). Only
            # flag when it's a *different* handler instance pointing at
            # what looks like the same underlying function -- which is
            # the shadow-import smell we want to catch. We approximate
            # "different handler" by requiring the command sets to be
            # disjoint AND one of them not to already be in our alias
            # allowlist.
            prev_cmds = seen[key]
            if prev_cmds.isdisjoint(handler.commands):
                duplicates.append(
                    f"{key[0]}.{key[1]} registered for both "
                    f"{sorted(prev_cmds)} and {sorted(handler.commands)}"
                )
        else:
            seen[key] = handler.commands

    # /agent and /agents are intentional aliases on cmd_agent. /help and /start
    # are intentional aliases on cmd_help. Filter those out of the failure
    # list -- they share command-name *prefixes* but the duplicate check
    # above already lets aliases through when commands overlap; we only
    # reach this list when the command sets are truly disjoint.
    allow_alias_pairs = {
        ("bot.commands.domain", "cmd_agent"),    # /agent + /agents
        ("bot.dispatcher", "cmd_help"),          # /help + /start
        ("bot.commands.project", "cmd_project"), # /project + /p
    }
    real_duplicates = [
        d for d in duplicates
        if not any(f"{m}.{n}" in d for (m, n) in allow_alias_pairs)
    ]

    assert not real_duplicates, (
        "Duplicate (module, name) callback registrations detected -- this "
        "is the shadow-import pattern that caused the /health bug:\n  "
        + "\n  ".join(real_duplicates)
    )
