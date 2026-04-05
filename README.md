# YOS — Personal AI Operating System

> A living, Telegram-accessible AI OS that acts as a compounding intelligence layer for everything you do.

YOS is a personal operating system built around Claude. It captures your ideas, tracks your goals, journals your moments, monitors your health, and will surface daily intelligence briefings on tech, business, and geopolitics — all accessible via a single Telegram bot. The system is designed to compound: every interaction makes it smarter about your priorities, patterns, and career.

---

## What It Does

- **Idea & Backlog Management** — capture product ideas via `/idea`, view prioritized backlog, score ideas with Claude AI
- **Goal Tracking** — set and track daily, weekly, quarterly, and yearly goals with progress bars
- **Daily Check-ins** — log mood and notes each day; track patterns over time
- **Journal / Moment Capture** — quick `/note` command to record wins, learnings, reflections instantly
- **Health Gap Detection** — log sleep, energy, and stress; bot reminds you if you've missed a day
- **Daily Dashboard** — `/today` shows active goals, today's briefing, and recent notes in one view
- **Persistent SQLite Store** — all data lives in a local DB covering ideas, goals, journal, health, career, and intelligence runs

---

## Architecture

```
Telegram Bot (python-telegram-bot)
        │
        ▼
bot/dispatcher.py ──► bot/commands/*.py
                              │
                              ▼
                    store/database.py  ←──  db/yos.db (SQLite)
                              │
                  utils/claude_client.py   (Anthropic SDK)
                  utils/telegram.py        (outbound messages)
                  utils/logger.py          (file + console logs)
```

Daily scheduler (Phase 2) will run intelligence agents → compose briefing → push to Telegram at 07:00.

---

## Project Structure

```
YOS/
├── store/
│   └── database.py        # Complete SQLite schema + DAL (ideas, goals, journal, health, career, intel)
├── bot/
│   ├── main.py            # Telegram bot entrypoint
│   ├── dispatcher.py      # Command handler registry + auth middleware
│   └── commands/
│       ├── ideas.py       # /idea, /backlog, /prioritize, /done
│       ├── goals.py       # /goal, /goals, /progress, /checkin
│       ├── journal.py     # /note, /journal
│       ├── health.py      # /health, /healthlog
│       └── today.py       # /today — daily dashboard
├── utils/
│   ├── claude_client.py   # Anthropic SDK wrapper (ask / ask_fast)
│   ├── telegram.py        # Outbound message helper
│   └── logger.py          # Daily rotating file + console logger
├── config/
│   └── settings.yaml      # Schedules, thresholds, model config
├── agents/                # (Phase 2) Tech, business, geopolitics intel agents
├── intelligence/          # (Phase 2) Daily briefing composer
├── integrations/          # (Phase 2) Gmail org read-only connector
├── scheduler/             # (Phase 2) 07:00 daily cron
├── web/                   # (Phase 5) FastAPI dashboard
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

---

## Usage

Once the bot is running, message it on Telegram:

| Command | Description |
|---|---|
| `/today` | Daily dashboard — goals, briefing, recent notes |
| `/idea <text>` | Capture idea to inbox backlog |
| `/backlog` | View top 10 prioritized ideas |
| `/prioritize <id>` | Score an idea with Claude AI |
| `/goal daily\|weekly\|quarterly\|yearly <title>` | Add a goal |
| `/goals` | All active goals with progress |
| `/progress <id> <0-100>` | Update goal progress |
| `/checkin <mood 1-5> [notes]` | Log daily check-in |
| `/note <text>` | Capture a moment (prefix: `win:`, `learning:`, `reflection:`) |
| `/journal [days]` | Recent journal entries |
| `/health <sleep> <energy> <stress> [notes]` | Log health data |
| `/healthlog` | Last 7 days health summary |
| `/brief` | Today's intelligence briefing (Phase 2) |
| `/help` | Full command reference |

---

## Configuration

| Variable | Description | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | Bot token | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Your personal chat ID | Message bot → call `getUpdates` |
| `DB_PATH` | SQLite database path | Default: `db/yos.db` |
| `GMAIL_ORG_DB_PATH` | Path to GmailOrganization DB | Default: `../GmailOrganization/learning/db/gmail_org.db` |

---

## Recent Changes

- `2026-04-05` — Initial YOS scaffold: CLAUDE.md vision + database schema

---

## Roadmap

- **Phase 2** — Intelligence agents (tech, business, geopolitics) + daily briefing at 07:00
- **Phase 3** — Career scanner (job matching vs. resume) + skill auto-tracking
- **Phase 4** — Health gap detection in morning briefing
- **Phase 5** — FastAPI web dashboard (backlog kanban, goal progress, briefing history)
- **Integration** — Gmail org connector: pull must-reads + charges into daily briefing
- **Resume versioning** — auto-update resume as you ship things and log skills
- **Monthly OS report** — what you built, learned, and what patterns emerged
