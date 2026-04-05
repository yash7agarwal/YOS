# YOS — Agent Operating System · v0.6.0

> A compounding personal intelligence system: captures ideas, tracks goals, runs daily intelligence agents, monitors career, and delivers everything through Telegram — getting smarter after every task.

YOS is built on the AOS (Agent Operating System) philosophy: not a task executor, but a system that compounds intelligence over time. Every agent run is evaluated, every pattern is stored, every decision is documented. The system improves itself week over month.

---

## What It Does

- **Daily Intelligence Briefing** — three agents (tech/AI, business, geopolitics) fetch live RSS feeds, synthesize with Claude, and deliver a structured briefing to Telegram every morning at 07:00 IST
- **Idea & Backlog Management** — capture ideas via `/idea`, view a prioritized backlog, score ideas with Claude AI scoring
- **Goal Tracking** — set and track daily, weekly, quarterly, and yearly goals with progress bars and check-ins
- **Journal / Moment Capture** — `/note` records wins, learnings, and reflections with auto-category detection
- **Career Intelligence** — job scanner matches against your profile, `/jobs`, `/resume`, `/skills` commands
- **Health Gap Detection** — log sleep, energy, stress; morning briefing includes a nudge if you've missed a day
- **Deep Research Agents** — multi-turn Claude Opus agents for weekly analysis, monthly reporting, and backlog curation
- **Compounding Memory** — every run is self-evaluated (Correctness/Efficiency/Reusability/Clarity 1-5) and stored; patterns, decisions, and learnings persist across conversations
- **Gmail Integration** — pulls must-read emails, recent charges, and renewal alerts from GmailOrganization's DB

---

## Architecture

```
AOS Layers
├── tools/          ← Execution layer: deterministic wrappers (db, ai, feeds, notify, eval)
├── workflows/      ← Instruction layer: SOPs for every pipeline
├── memory/         ← Intelligence layer: learnings, patterns, decisions, user context
├── agents/         ← Decision layer: feed-based intel + deep Opus research agents
│
Telegram (@YOperatingSystem_BOT)
        │
        ▼
bot/dispatcher.py ──► bot/commands/*.py
        │
        ├── store/database.py  ←── db/yos.db (SQLite, WAL mode, 14 tables)
        ├── utils/claude_client.py   (Sonnet default, Opus for deep agents)
        ├── utils/telegram.py
        └── integrations/gmail.py   (read-only GmailOrg DB)

scheduler/main.py (APScheduler, Asia/Kolkata)
        ├── 07:00 daily   → agents → briefing → Telegram
        ├── Mon 08:15     → weekly_analyst (Opus, multi-turn)
        ├── 1st 09:00     → monthly_reporter (Opus, multi-turn)
        └── every 6h      → system_health (PID check + auto-restart)
```

---

## Project Structure

```
YOS/
├── memory/                    # AOS compounding intelligence
│   ├── learnings.md           # Mistakes, fixes, operational insights
│   ├── patterns.md            # Reusable approaches and solutions
│   ├── decisions.md           # Architecture decision rationale
│   └── user_context.md        # Preferences, tokens, project context
│
├── workflows/                 # Instruction layer: SOPs
│   ├── daily_briefing.md
│   ├── weekly_analysis.md
│   ├── monthly_report.md
│   ├── backlog_curation.md
│   └── system_health.md
│
├── tools/                     # Execution layer: deterministic wrappers
│   ├── db.py                  # All DB reads/writes
│   ├── ai.py                  # All Claude API calls
│   ├── feeds.py               # RSS feed ingestion (feedparser)
│   ├── notify.py              # Telegram outbound
│   └── eval.py                # AOS self-evaluation scoring
│
├── store/
│   └── database.py            # SQLite schema + DAL (14 tables incl. evaluations)
│
├── bot/
│   ├── main.py                # Bot entrypoint
│   ├── dispatcher.py          # Command registry + auth
│   └── commands/              # ideas, goals, journal, health, intel, career, today
│
├── agents/
│   ├── tech_intel.py          # HN + AI RSS → 6 bullets (Sonnet)
│   ├── biz_intel.py           # Yahoo Finance RSS → 5 insights (Sonnet)
│   ├── geo_intel.py           # BBC + Reuters → 4 bullets (Sonnet)
│   └── claude/
│       ├── runner.py          # Generic Opus tool-use loop + self-eval
│       ├── tools.py           # 7 tools: web_search, fetch_url, query_yos_db, etc.
│       ├── backlog_curator.py # Deep backlog curation agent
│       ├── weekly_analyst.py  # Weekly synthesis agent
│       ├── monthly_reporter.py# Monthly OS report agent
│       └── system_health.py   # Process health + auto-restart
│
├── intelligence/
│   └── briefing.py            # Compose + save + send daily briefing
│
├── integrations/
│   └── gmail.py               # Read-only GmailOrg SQLite access
│
├── scheduler/
│   ├── main.py                # All APScheduler jobs + CLI flags
│   ├── daily.py               # Daily pipeline
│   ├── weekly.py              # Weekly analysis
│   └── monthly.py             # Monthly report
│
├── web/
│   ├── app.py                 # FastAPI + Jinja2
│   └── routers/               # backlog, goals, intel, career
│
├── utils/
│   ├── claude_client.py       # Anthropic SDK wrapper (retry, model selection)
│   ├── telegram.py            # Outbound message helper
│   └── logger.py              # Daily rotating file + console logger
│
├── .tmp/                      # Disposable/regenerable files (gitignored)
├── config/settings.yaml
├── .env.example
└── requirements.txt
```

---

## Setup

1. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Fill in all values
   ```

3. **Initialize the database**
   ```bash
   python3 -c "from store.database import init_db; init_db()"
   ```

4. **Start the bot**
   ```bash
   nohup python3 -m bot.main > logs/daily/bot.log 2>&1 &
   ```

5. **Start the scheduler** (daily briefing at 07:00 IST)
   ```bash
   nohup python3 -m scheduler.main > logs/daily/scheduler.log 2>&1 &
   ```

6. **Trigger a manual briefing**
   ```bash
   python3 -m scheduler.main --now
   ```

7. **Start the web dashboard** (optional)
   ```bash
   nohup python3 -m web.app > logs/daily/web.log 2>&1 &
   # Open http://localhost:8000
   ```

---

## Usage

Message `@YOperatingSystem_BOT` on Telegram:

| Command | Description |
|---|---|
| `/today` | Daily dashboard — goals, briefing excerpt, health status |
| `/idea <text>` | Capture idea to inbox backlog |
| `/backlog` | Top 10 prioritized ideas |
| `/prioritize <id>` | Score an idea with Claude |
| `/done <id>` | Mark idea complete |
| `/goal daily\|weekly\|quarterly\|yearly <title>` | Add a goal |
| `/goals` | All active goals with progress bars |
| `/progress <id> <0-100>` | Update goal progress |
| `/checkin <mood 1-5> [notes]` | Log daily check-in |
| `/note <text>` | Capture a moment |
| `/journal [days]` | Recent journal entries |
| `/health <sleep> <energy> <stress>` | Log health data |
| `/healthlog` | Last 7 days health summary |
| `/brief` | Full daily intelligence briefing |
| `/tech` `/biz` `/geo` | Individual agent summaries |
| `/run` | Manually trigger all agents + briefing |
| `/weekly` | Trigger weekly deep analysis |
| `/monthly` | Trigger monthly OS report |
| `/jobs` | Top career matches |
| `/skills` | Skill map |
| `/syshealth` | Process health status |
| `/help` | Full command reference |

---

## Configuration

| Variable | Description | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | YOS bot token | @BotFather → `/newbot` |
| `TELEGRAM_CHAT_ID` | Your personal chat ID | Send any message to bot → `getUpdates` |
| `DB_PATH` | SQLite database path | Default: `db/yos.db` |
| `GMAIL_ORG_DB_PATH` | Path to GmailOrganization DB | Default: `../GmailOrganization/learning/db/gmail_org.db` |

---

## AOS Compounding Loop

After every meaningful agent run:

1. Output is self-evaluated on 4 dimensions (1-5): Correctness, Efficiency, Reusability, Clarity
2. Scores saved to `evaluations` table for trend analysis
3. Patterns extracted to `memory/patterns.md`
4. Learnings stored in `memory/learnings.md`
5. Workflows updated when a better method is discovered

The system improves its decision quality over time, not just completes tasks.

---

## Recent Changes

- `2026-04-06` — AOS rework: memory/, workflows/, tools/ layers; evaluations table; self-eval in runner
- `2026-04-06` — Add semantic versioning: VERSION, CHANGELOG.md, v0.5.0
- `2026-04-06` — Add Claude multi-step agents for deep research and system health
- `2026-04-06` — Implement Phase 3-5: career scanner, health alerts, and web dashboard
- `2026-04-06` — Implement Phase 2: Intelligence agents, daily briefing, and Gmail integration

---

## Roadmap

- Monthly spend report — total by merchant and category pulled from GmailOrg
- FastAPI web dashboard Phase 2 — Kanban backlog, briefing history timeline
- Resume auto-update — extract skills from `/note` and `/idea` entries
- Monthly OS report surfaced in Telegram as structured digest
- GmailOrg deeper integration — AI tool discoveries → YOS knowledge base
- Evaluation trend dashboard — /syshealth shows avg scores per agent over time
- Cross-device sync (multiple machines reading same DB via sync tool)

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI | Claude claude-sonnet-4-6 (default) + claude-opus-4-6 (deep agents) |
| Notifications | Telegram Bot API (`python-telegram-bot` v20+) |
| Storage | SQLite + WAL (`store/database.py`, 14 tables) |
| Scheduling | APScheduler (CronTrigger, Asia/Kolkata) |
| Web UI | FastAPI + Jinja2 + Tailwind CDN |
| Feed ingestion | feedparser |
| Language | Python 3.9+ |
