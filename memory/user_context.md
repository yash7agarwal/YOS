# User Context — Preferences, Constraints, and Project Context

---

## User Profile

- **Primary interface:** Telegram (mobile-first, always-on)
- **Development machine:** macOS (Darwin 25.4.0)
- **Python:** 3.9+ (use `from __future__ import annotations`; no backslash in f-strings)
- **Shell:** zsh; uses `python3` and `pip3` (not `python` / `pip`)
- **AI tooling:** Heavy Claude user; building around Anthropic SDK; understands tool-use loops

## Current Projects

| Project | Path | Purpose | Status |
|---|---|---|---|
| YOS / AOS | `/Users/yash/ClaudeWorkspace/YOS` | Personal AI Operating System | Active — main project |
| GmailOrganization | `/Users/yash/ClaudeWorkspace/GmailOrganization` | Autonomous inbox management | Active — independent |

## Bot Tokens (one per project)

| Bot | Token prefix | Project |
|---|---|---|
| @YOperatingSystem_BOT | `8602530979:AAH...` | YOS |
| GmailOrg bot | `8634920054:...` | GmailOrganization |
| Telegram Chat ID | `8568125947` | Both projects — same user |

## YOS Database

- Path: `db/yos.db` (relative to YOS project root)
- 13 tables: ideas, goals, checkins, journal, health_logs, job_listings, resume_versions, skills, agent_runs, briefings, bot_interactions, evaluations (added v0.6.0)

## GmailOrg Integration

- Read-only via SQLite: `../GmailOrganization/learning/db/gmail_org.db`
- Always check `os.path.exists(GMAIL_DB)` before connecting — graceful degradation

## User Preferences

- **Responses should be terse** — no trailing summaries, no recapping what was done
- **No emojis in code or documentation** unless explicitly asked
- **No comments in code** unless logic is non-obvious
- **No speculative abstractions** — build what is needed now
- **Commit messages in imperative mood** — "Add X", "Fix Y", not "Added X"
- **Version bumps:** new features → minor, bug fixes → patch, explicit request → major

## Operating Philosophy (AOS CLAUDE.md)

The user treats YOS as a **compounding intelligence system**, not just a task executor. Every task should improve at least one part of the system. The four optimization dimensions:
1. Correctness
2. Efficiency  
3. Reusability
4. Decision Quality

The system must not treat every task as a first-time problem. Always check memory/ before generating fresh output.

## Key Constraint — Python 3.9 Compatibility

The following are illegal in Python 3.9:
- Backslash in f-string curly braces: `f"{'\n'.join(x)}"` → pre-assign
- `list[str]` type hints without `from __future__ import annotations`
- `match`/`case` statements (Python 3.10+)

## Scheduling

- Daily briefing: 07:00 IST (Asia/Kolkata)
- Weekly analysis: Monday 08:15 IST
- Monthly report: 1st of month 09:00 IST
- Health check: every 6 hours
- Scheduler: APScheduler in-process (not OS cron, not RemoteTrigger)

## Last Updated

2026-04-06 — initial population from full build session (Phase 1–5 + AOS rework)
