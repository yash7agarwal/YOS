# Changelog

All notable changes are documented here following [Semantic Versioning](https://semver.org/).

## [0.5.0] — 2026-04-06
### Added
- Claude multi-step agent runner with tool-use loop (up to 15 turns, Opus/Sonnet)
- `weekly_analyst` — every Monday, deep-searches AI/tech/business news, adds backlog ideas, saves learnings
- `monthly_reporter` — 1st of month, reviews all goals/journal/health/career, surfaces patterns, sends OS report
- `backlog_curator` — every Sunday, scores all inbox ideas vs goals + market signals, picks top 3 to start
- `system_health` — every 6h, checks all process PIDs and auto-restarts dead services
- 7 agent tools: `web_search`, `fetch_url`, `query_yos_db`, `add_idea`, `save_journal`, `set_idea_priority`, `send_telegram`
- Bot commands: `/weekly`, `/monthly`, `/syshealth` for manual agent triggers
- `scheduler/weekly.py` and `scheduler/monthly.py` pipeline wrappers
- PID file management for bot, scheduler, and web processes

## [0.4.0] — 2026-04-06
### Added
- Career scanner agent scanning HN Jobs, RemoteOK, WeWorkRemotely daily
- Bot commands: `/jobs`, `/apply`, `/skills`, `/skill`, `/resume`
- FastAPI web dashboard on port 8000 (dark UI with Tailwind CSS)
- Pages: Intelligence briefing, Backlog kanban, Goal progress, Career board
- Health gap alert and top job match embedded in daily briefing
- `python-multipart` dependency for FastAPI form handling

## [0.3.0] — 2026-04-06
### Added
- Three intelligence agents: `tech_intel` (HN RSS), `biz_intel` (Yahoo Finance), `geo_intel` (BBC/Reuters)
- `intelligence/briefing.py` — composes and caches daily briefing from all agents
- `integrations/gmail.py` — read-only GmailOrg DB connector (must-reads, charges, renewals)
- `scheduler/daily.py` and `scheduler/main.py` with APScheduler at 07:00 IST
- Bot commands: `/brief`, `/tech`, `/biz`, `/geo`, `/run`
- `feedparser` and `apscheduler` dependencies

## [0.2.0] — 2026-04-06
### Added
- Telegram bot (`@YOperatingSystem_BOT`) with full command dispatcher and auth middleware
- Bot commands: `/idea`, `/backlog`, `/prioritize`, `/done` (backlog management)
- Bot commands: `/goal`, `/goals`, `/progress`, `/checkin` (goal tracking)
- Bot commands: `/note`, `/journal` (moment capture with auto-category detection)
- Bot commands: `/health`, `/healthlog` (health logging with gap detection)
- Bot command: `/today` daily dashboard (goals + briefing + notes + health nudge)
- `utils/claude_client.py` with retry logic, `utils/telegram.py`, `utils/logger.py`
- `config/settings.yaml` with model config and schedule thresholds

## [0.1.0] — 2026-04-06
### Added
- Initial YOS scaffold: `CLAUDE.md` vision document
- Complete SQLite schema (`store/database.py`) covering ideas, goals, journal, health, career, intel, briefings, and bot interactions
- Project directory structure: `agents/`, `bot/`, `intelligence/`, `integrations/`, `scheduler/`, `web/`, `utils/`, `config/`
