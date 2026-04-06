# YOS — Agent Operating System · v0.7.0

> A compounding personal intelligence system and product-building OS: captures ideas, generates PRDs, tracks goals, runs daily intelligence agents, and delivers everything through Telegram and a live web dashboard.

YOS is built on the AOS (Agent Operating System) philosophy — every agent run is evaluated, every pattern is stored, every decision is documented. The system improves itself week over month. Version 0.7.0 adds the Product OS: a living PRD platform where ideas cluster into structured specs that evolve via natural language commands.

---

## What It Does

- **Daily Intelligence Briefing** — three agents (tech/AI, business, geopolitics) fetch live RSS feeds, synthesize with Claude, and deliver a structured briefing to Telegram at 07:00 IST
- **Product OS** — `prd-builder` skill clusters backlog ideas into themes, generates full PRDs, and exposes a web platform where you can comment and issue live development commands that Claude executes against the spec
- **Idea & Backlog Management** — capture ideas via `/idea`, view prioritized backlog, score with Claude
- **Goal Tracking** — daily, weekly, quarterly, and yearly goals with progress bars and check-ins
- **Journal / Moment Capture** — `/note` records wins, learnings, and reflections with auto-category detection
- **Career Intelligence** — job scanner matches against your profile; `/jobs`, `/resume`, `/skills` commands
- **Health Gap Detection** — log sleep, energy, stress; morning briefing nudges if you've missed a day
- **Deep Research Agents** — multi-turn Claude Opus agents for weekly analysis, monthly reporting, backlog curation
- **Compounding Memory** — every run self-evaluates (Correctness/Efficiency/Reusability/Clarity 1–5); patterns, decisions, and learnings persist across conversations
- **Auto-start on boot** — macOS launchd services keep all processes alive across reboots and crashes

---

## Architecture

```
AOS Layers
├── tools/          ← Execution layer: db, ai, feeds, notify, eval
├── workflows/      ← SOPs for every pipeline
├── memory/         ← learnings, patterns, decisions, user context
│
Telegram (@YOperatingSystem_BOT) + Web (localhost:8000)
        │
        ▼
bot/dispatcher.py ──► bot/commands/*.py
        │
        ├── store/database.py  ←── db/yos.db (SQLite, WAL, 17 tables)
        ├── utils/claude_client.py   (Sonnet default, Opus for deep agents)
        └── integrations/gmail.py   (read-only GmailOrg DB)

scheduler/main.py (APScheduler, Asia/Kolkata) — launchd managed
        ├── 07:00 daily   → agents → briefing → Telegram
        ├── Mon 08:15     → weekly_analyst (Opus)
        ├── 1st 09:00     → monthly_reporter (Opus)
        └── every 6h      → system_health check

~/.claude/skills/prd-builder/  ← Cluster backlog → generate PRDs → save + notify
web/routers/product.py         ← /product, /product/prd/{id}, dev commands
```

---

## Project Structure

```
YOS/
├── memory/                    # AOS: learnings, patterns, decisions, user_context
├── workflows/                 # SOPs: daily_briefing, weekly, monthly, backlog, health
├── tools/                     # Execution wrappers: db, ai, feeds, notify, eval
│
├── store/database.py          # SQLite DAL — 17 tables incl. idea_clusters, prds, prd_comments
│
├── bot/
│   ├── main.py / dispatcher.py
│   └── commands/              # ideas, goals, journal, health, intel, career, today
│
├── agents/
│   ├── tech_intel.py / biz_intel.py / geo_intel.py   # feed-based (Sonnet)
│   └── claude/
│       ├── runner.py          # Generic Opus tool-use loop + self-eval
│       ├── tools.py           # 7 tools: web_search, fetch_url, query_yos_db, etc.
│       ├── backlog_curator.py / weekly_analyst.py
│       ├── monthly_reporter.py / system_health.py
│
├── intelligence/briefing.py   # Compose + save + send daily briefing
├── integrations/gmail.py      # Read-only GmailOrg SQLite
│
├── scheduler/main.py          # APScheduler jobs + --now/--weekly/--monthly flags
│
├── web/
│   ├── app.py                 # FastAPI + Jinja2
│   ├── routers/               # backlog, goals, intel, career, product
│   └── templates/             # base, backlog, goals, intel, career, product, prd_detail
│
├── utils/                     # claude_client, telegram, logger
├── config/settings.yaml
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
   cp .env.example .env  # fill in API keys
   ```

3. **Initialize database**
   ```bash
   python3 -c "from store.database import init_db; init_db()"
   ```

4. **Register launchd services** (auto-start on login/boot)
   ```bash
   launchctl load ~/Library/LaunchAgents/com.yos.bot.plist
   launchctl load ~/Library/LaunchAgents/com.yos.scheduler.plist
   launchctl load ~/Library/LaunchAgents/com.yos.web.plist
   ```

5. **Trigger manual briefing**
   ```bash
   python3 -m scheduler.main --now
   ```

6. **Generate PRDs from backlog** (in Claude Code)
   ```
   cluster my backlog
   ```

---

## Usage

### Telegram — `@YOperatingSystem_BOT`

| Command | Description |
|---|---|
| `/today` | Daily dashboard |
| `/idea <text>` | Capture idea |
| `/backlog` | Top 10 prioritized ideas |
| `/goal daily\|weekly\|quarterly\|yearly <title>` | Add goal |
| `/goals` / `/progress <id> <0-100>` | Goals + progress |
| `/note <text>` | Journal entry |
| `/health <sleep> <energy> <stress>` | Log health |
| `/brief` / `/tech` / `/biz` / `/geo` | Intelligence briefing |
| `/run` / `/weekly` / `/monthly` | Trigger agents |
| `/jobs` / `/skills` / `/resume` | Career module |
| `/syshealth` | Process health |

### Web Dashboard — `http://localhost:8000`

| Page | URL | What it shows |
|---|---|---|
| Intelligence | `/intel` | Daily briefing + agent status |
| Backlog | `/backlog` | Kanban board (inbox → done) |
| Goals | `/goals` | Progress dashboard |
| Career | `/career` | Jobs + skills + resume |
| **Product OS** | `/product` | Clusters + PRD cards |
| **PRD Detail** | `/product/prd/{id}` | Full spec + comment thread + live command terminal |

### PRD Command Terminal

On any PRD detail page, type natural language commands:
- `"Add authentication requirements"` → updates requirements section
- `"Generate user stories for mobile"` → rewrites user stories
- `"What are the key risks?"` → analysis response in thread
- `"Refine goals to be more measurable"` → updates goals section

---

## Configuration

| Variable | Description | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | YOS bot token | @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID | Send message → `getUpdates` |
| `DB_PATH` | SQLite path | Default: `db/yos.db` |
| `GMAIL_ORG_DB_PATH` | GmailOrg DB | Default: `../GmailOrganization/learning/db/gmail_org.db` |

---

## Changelog

- `v0.7.0` — Product OS: prd-builder skill, /product web section, live PRD command terminal
- `v0.6.1` — macOS launchd auto-start for all 3 YOS services
- `v0.6.0` — AOS rework: memory/, workflows/, tools/ layers; evaluations table; self-eval runner
- `v0.5.0` — Claude multi-step agents (weekly analyst, monthly reporter, system health)
- `v0.4.0` — Career scanner, FastAPI web dashboard, health gap detection

---

## Roadmap

- Design language + app ecosystem (next)
- VPS deployment — Dockerfile + systemd for 24/7 cloud operation (backlog #3)
- Resume auto-update from `/note` and `/idea` skill extractions
- Monthly OS report as structured Telegram digest
- Evaluation trend dashboard — `/syshealth` shows avg agent scores over time
- PRD → GitHub Issues export (auto-create issues from requirements)
- Cross-device DB sync
