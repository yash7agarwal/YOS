# Changelog

All notable changes are documented here following [Semantic Versioning](https://semver.org/).

## [0.9.2] — 2026-04-19 — Frontend design refresh + hardening

### Added
- `DESIGN.md` — formalizes the CSS variables system and visual rules adopted in this release.

### Changed
- `web/templates/base.html` — introduced CSS variables design system: Satoshi sans + JetBrains Mono, calibrated dark palette (`--bg`, `--surface-1/2`, `--border*`, `--text*`, `--accent`), cubic-bezier progress-bar easing. Replaces the ad-hoc "bg-gray-800 + Inter" styling.
- `web/templates/backlog.html`, `career.html`, `goals.html`, `intel.html`, `prd_detail.html`, `product.html` — realigned to the new variables and typography.

### Fixed
- `bot/dispatcher.py` — stopped leaking raw exception text to Telegram users; replaced with a generic "check server logs for details" message.
- `utils/claude_client.py` — `_get_client()` now raises a clear RuntimeError when `ANTHROPIC_API_KEY` is missing instead of cryptic KeyError.
- `web/routers/backlog.py` — `POST /api/backlog/{id}/status` validates against the allowed set and returns 400 on invalid input.

### Migration notes
No schema or API contract changes. Upgrading is drop-in.

## [0.9.1] — 2026-04-11
### Added
- `memory/issues_log.jsonl` — initialized for the cross-project self-healing system; receives eval pass/fail entries and known-issue patterns from `/post-task-eval` and `/self-heal` skills

## [0.9.0] — 2026-04-09
### Added
- CLAUDE.md: Context Window Preservation section — mandatory subagent delegation protocol with rules, anti-patterns, and prompt template
- `.claude/agents/premium-experience-curator.md` — new domain agent for premium experience curation

### Changed
- CLAUDE.md: Strengthened operating rules with explicit subagent delegation as the default behavior

## [0.8.0] — 2026-04-07
### Added
- 6 domain agents (Finance, Product, Strategy, Research, Contrarian, Creative) in `agents/domain/`
- `/agent`, `/ask`, `/reset` Telegram commands for conversational domain agent switching
- `user_agent_state` SQLite table with persistent conversation history (last 20 turns)
- `ask_local()` and `ask_auto()` in `utils/claude_client.py` for Ollama/Gemma 4 local inference
- `Dockerfile` and `docker-compose.yml` for VPS containerised deployment
- Fixed Jinja2 macro ordering bug in `product.html` and `prd_detail.html` (macros must precede use)
- Fixed PRD command terminal JSON truncation: two-call approach (routing + content generation)
- Rewrote `system_health.py` to be launchd-aware (uses `launchctl list/kickstart`, no PID files)
### Changed
- `store/database.py` — added `user_agent_state` table + 4 DAL functions
- `bot/dispatcher.py` — registered domain agent command handlers
- `.env.example` — added `INFERENCE_MODE` and `OLLAMA_HOST` vars

## [0.7.0] — 2026-04-06
### Added
- Product OS web section: `/product` — cluster cards with PRD listings and status badges
- PRD detail view: `/product/prd/{id}` — all 8 PRD sections with inline editing
- Live command terminal on each PRD: type natural language commands, Claude updates sections in real-time
- Comment/note thread on each PRD with user and Claude entries (color-coded by author and type)
- `prd-builder` skill at `~/.claude/skills/prd-builder/` — clusters backlog ideas + generates PRDs end-to-end
- 3 new SQLite tables: `idea_clusters`, `prds`, `prd_comments`
- 9 new DAL functions in `store/database.py` for Product OS
- `web/routers/product.py` with 5 routes (list, detail, comment, command, status)
### Changed
- `web/app.py` — registered product router
- `web/templates/base.html` — added "Product OS" nav link
- `memory/learnings.md` — added L-013 (Telegram Markdown fallback) and L-014 (launchd duplicate processes)

## [0.6.1] — 2026-04-06
### Added
- macOS launchd services: `com.yos.bot` and `com.yos.scheduler` auto-start on login/boot with KeepAlive restart
- Backlog idea #3: VPS cloud deployment for 24/7 operation (logged via /idea)

## [0.6.0] — 2026-04-06
### Added
- AOS rework: `memory/` layer with learnings.md, patterns.md, decisions.md, user_context.md — populated from full build session
- `workflows/` layer with SOPs for daily_briefing, weekly_analysis, monthly_report, backlog_curation, system_health
- `tools/` execution layer: db.py, ai.py, feeds.py, notify.py, eval.py — deterministic wrappers over utils/store
- `evaluations` table in SQLite (Correctness/Efficiency/Reusability/Clarity 1-5 per agent run)
- `tools/eval.py` — AOS compounding loop: Claude self-evaluates every meaningful agent output
- `.tmp/` directory (disposable/regenerable files, gitignored)
### Changed
- `agents/claude/runner.py` — auto self-evaluates every run after completion
- `store/database.py` — added evaluations table + save_evaluation/get_evaluation_summary functions
- `.gitignore` — added .tmp/ exclusion rule

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
