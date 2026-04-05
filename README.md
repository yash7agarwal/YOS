# YOS — Personal AI Operating System

> A living, Telegram-accessible AI OS that compounds intelligence across ideas, goals, health, career, and daily briefings.

YOS is a personal operating system built on Claude. It captures ideas, tracks goals, journals moments, monitors health, and delivers a daily intelligence briefing on tech, AI, business, and geopolitics — all through a dedicated Telegram bot (`@YOperatingSystem_BOT`). Every interaction is persisted to a local SQLite store, designed to compound in value over time.

YOS runs alongside the separate GmailOrganization system, pulling inbox highlights, recent charges, and renewal alerts into its daily briefing.

---

## What It Does

- **Daily Intelligence Briefing** — three agents (tech/AI, business, geopolitics) fetch from live RSS feeds, synthesize with Claude, and deliver a structured briefing to Telegram every morning at 07:00 IST
- **Gmail Integration** — pulls must-read emails, recent charges, and upcoming renewals from GmailOrganization's DB into the briefing
- **Idea & Backlog Management** — capture product ideas via `/idea`, view a prioritized backlog, score ideas with Claude AI
- **Goal Tracking** — set and track daily, weekly, quarterly, and yearly goals with progress bars and check-ins
- **Journal / Moment Capture** — `/note` command records wins, learnings, and reflections with auto-category detection
- **Health Gap Detection** — log sleep, energy, and stress; morning briefing nudges if you've missed a day
- **Daily Dashboard** — `/today` aggregates active goals, today's briefing excerpt, recent notes, and health status in one view
- **Persistent SQLite Store** — all data (ideas, goals, journal, health, career, intel runs, briefings) lives in a local DB

---

## Architecture

```
Telegram (@YOperatingSystem_BOT)
        │
        ▼
bot/dispatcher.py ──► bot/commands/*.py
        │
        ├── store/database.py  ←──  db/yos.db (SQLite)
        │
        ├── utils/claude_client.py   (Anthropic claude-sonnet-4-6)
        ├── utils/telegram.py        (outbound messages)
        └── utils/logger.py          (daily rotating logs)

scheduler/main.py (07:00 IST daily)
        │
        ▼
agents/tech_intel.py  ──► HN RSS + AI feeds → Claude synthesis
agents/biz_intel.py   ──► Yahoo Finance RSS → Claude synthesis
agents/geo_intel.py   ──► BBC World + Reuters → Claude synthesis
        │
        ▼
intelligence/briefing.py  ──► compose + save + send to Telegram
        │
integrations/gmail.py     ──► read-only GmailOrg SQLite DB
```

---

## Project Structure

```
YOS/
├── store/
│   └── database.py          # Full SQLite schema + DAL (ideas, goals, journal, health, career, intel)
├── bot/
│   ├── main.py              # Bot entrypoint (python-telegram-bot, polling)
│   ├── dispatcher.py        # Command registry + auth + interaction logging
│   └── commands/
│       ├── ideas.py         # /idea, /backlog, /prioritize, /done
│       ├── goals.py         # /goal, /goals, /progress, /checkin
│       ├── journal.py       # /note, /journal
│       ├── health.py        # /health, /healthlog
│       ├── intel.py         # /brief, /tech, /biz, /geo, /run
│       └── today.py         # /today — daily dashboard
├── agents/
│   ├── base.py              # Shared run/save wrapper → agent_runs table
│   ├── tech_intel.py        # HN frontpage + AI RSS → 6 signal bullets
│   ├── biz_intel.py         # Yahoo Finance + startup RSS → 5 business insights
│   └── geo_intel.py         # BBC World + Reuters → 4 geopolitical bullets
├── intelligence/
│   └── briefing.py          # Compose briefing from agents + Gmail; save + send
├── integrations/
│   └── gmail.py             # Read-only GmailOrg DB (must-reads, charges, renewals)
├── scheduler/
│   ├── main.py              # APScheduler at 07:00 IST; --now for manual trigger
│   └── daily.py             # Full pipeline: agents → briefing → Telegram
├── utils/
│   ├── claude_client.py     # Anthropic SDK wrapper (ask / ask_fast with retry)
│   ├── telegram.py          # Outbound message helper
│   └── logger.py            # Daily rotating file + console logger
├── config/
│   └── settings.yaml        # Schedules, model config, thresholds
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
   python3 -m bot.main
   ```

5. **Start the scheduler** (daily briefing at 07:00 IST)
   ```bash
   python3 -m scheduler.main
   ```

6. **Trigger a manual briefing run**
   ```bash
   python3 -m scheduler.main --now
   ```

---

## Usage

Message `@YOperatingSystem_BOT` on Telegram:

| Command | Description |
|---|---|
| `/today` | Daily dashboard — goals, briefing excerpt, notes, health status |
| `/idea <text>` | Capture idea to inbox backlog |
| `/backlog` | Top 10 prioritized ideas |
| `/prioritize <id>` | Score an idea with Claude |
| `/done <id>` | Mark idea complete |
| `/goal daily\|weekly\|quarterly\|yearly <title>` | Add a goal |
| `/goals` | All active goals with progress bars |
| `/progress <id> <0-100>` | Update goal progress |
| `/checkin <mood 1-5> [notes]` | Log daily check-in |
| `/note <text>` | Capture a moment (`win:`, `learning:`, `reflection:` prefixes) |
| `/journal [days]` | Recent journal entries |
| `/health <sleep> <energy> <stress> [notes]` | Log health data |
| `/healthlog` | Last 7 days health summary |
| `/brief` | Full daily intelligence briefing |
| `/tech` | Tech & AI agent summary |
| `/biz` | Business & markets snapshot |
| `/geo` | Geopolitics briefing |
| `/run` | Manually trigger all agents + generate briefing |
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

## Recent Changes

- `2026-04-06` — Implement Phase 2: Intelligence agents, daily briefing, and Gmail integration
- `2026-04-06` — Implement Phase 1: Telegram bot core with backlog, goals, journal, and health
- `2026-04-06` — Initial YOS scaffold

---

## Roadmap

- **Phase 3** — Career scanner: job matching vs. resume profile, `/jobs`, `/resume`, `/skills` commands, skill auto-extraction from notes
- **Phase 4** — Health gap detection surfaced in morning briefing
- **Phase 5** — FastAPI web dashboard: backlog kanban, goal progress, briefing history
- **Career** — Resume versioning: auto-update as you ship things and log skills
- **Monthly OS Report** — what you built, learned, and what patterns emerged
- **GmailOrg deeper integration** — AI tool discoveries from emails → YOS knowledge base
