# Decisions — Key Architecture Choices and Rationale

Rationale for non-obvious design decisions. Referenced when evaluating change proposals.

---

## D-001 — GmailOrganization stays a separate project

**Decision:** YOS does not absorb GmailOrganization. Integration is read-only via shared SQLite.

**Why:** GmailOrganization has its own Telegram bot, cron schedule, OAuth tokens, and learning loop. Merging them would create a monolith with complex dependencies, dual OAuth flows, and a single point of failure. The inbox system must work independently even if YOS is down.

**Trade-off accepted:** Slightly redundant infrastructure (two bots, two schedulers). Worth the separation of concerns.

**How to apply:** Never write to GmailOrg DB from YOS. Never import GmailOrg Python modules. Integration = `os.path.exists(GMAIL_DB)` + read-only SQL.

---

## D-002 — SQLite over PostgreSQL

**Decision:** Single SQLite file (`db/yos.db`) with WAL mode.

**Why:** Single-user system. No concurrent writes from multiple machines. SQLite with WAL handles concurrent reads + writes from bot + scheduler adequately. Zero infrastructure to maintain, no connection strings, trivially backed up by copying one file.

**Trade-off accepted:** Not horizontally scalable. Acceptable — this is a personal OS for one user.

**How to apply:** If multi-user or multi-device is ever needed, migrate to PostgreSQL. Until then, keep SQLite.

---

## D-003 — claude-sonnet-4-6 default, claude-opus-4-6 for deep agents

**Decision:** `DEFAULT_MODEL = "claude-sonnet-4-6"` for all standard calls. `DEEP_MODEL = "claude-opus-4-6"` only for multi-turn tool-use agents (weekly analyst, monthly reporter, career scanner).

**Why:** Sonnet provides 90%+ of Opus quality at 20% the cost for structured outputs. Daily briefing agents (tech/biz/geo) are feed-based and don't need multi-turn reasoning. Deep research agents (backlog curator, weekly analyst) benefit from Opus's reasoning depth.

**How to apply:** When adding a new agent, ask: "Does this need multi-turn tool use?" If no → Sonnet. If yes → Opus.

---

## D-004 — APScheduler over cron for scheduling

**Decision:** Use APScheduler (in-process, CronTrigger) rather than OS cron or RemoteTrigger.

**Why:** RemoteTrigger is limited to 1 slot per plan (already used by GmailOrg). OS cron requires writing to system crontab, which breaks on new machines and lacks visibility. APScheduler runs inside the Python process, is timezone-aware, and observable via logs.

**Trade-off accepted:** Scheduler only runs while the process is alive. System health monitor (`agents/claude/system_health.py`) checks every 6h and restarts dead processes.

**How to apply:** All scheduling through `scheduler/main.py` → APScheduler. One-off manual runs via `python3 -m scheduler.main --now`.

---

## D-005 — Telegram as primary interface (not web)

**Decision:** Telegram is the primary user interface. Web dashboard is secondary/optional.

**Why:** Telegram is always accessible on mobile. Commands have instant gratification (no URL navigation). Push notifications are native. The user already uses Telegram daily. Web dashboard adds friction for quick lookups.

**How to apply:** New features should be Telegram-first. Web routers are bonus visualization, not primary workflows.

---

## D-006 — feedparser over httpx for all RSS ingestion

**Decision:** Use `feedparser.parse(url)` for all RSS/Atom feed consumption.

**Why:** feedparser handles all RSS variants (0.9, 1.0, 2.0), Atom, malformed XML, charset detection, and date normalization. httpx + manual BeautifulSoup XML parsing is fragile and reinvents what feedparser already solves.

**How to apply:** Any new agent consuming news/blog feeds uses `feedparser`. httpx is reserved for non-RSS URLs (arbitrary HTML scraping).

---

## D-007 — Tailwind CDN for web UI (no build step)

**Decision:** Web templates use Tailwind CSS via CDN `<script>`, no npm/webpack/build step.

**Why:** This is a personal tool, not a production SaaS. A build pipeline would add maintenance overhead with zero user benefit. CDN Tailwind is fast enough for local use.

**Trade-off accepted:** Slower first load on cold cache. Acceptable for single-user local web app.

**How to apply:** Never introduce a build step (npm, webpack, vite) unless the user explicitly requests it.

---

## D-008 — AOS memory system over inline documentation

**Decision:** Use `memory/` directory with structured markdown files instead of inline comments or separate docs.

**Why:** Inline comments are buried and not consulted before starting new tasks. The CLAUDE.md AOS model treats `memory/` as a first-class system layer — inspected at the start of every task via System Navigation Protocol. This creates compounding intelligence rather than one-off notes.

**How to apply:** After every meaningful task, update at least one file in `memory/`. Patterns that appear twice must be stored. The system is stagnating if nothing improves after a task.

---

## D-009 — Two Telegram bots, not one

**Decision:** GmailOrganization uses its own bot (`@GmailOrgBot`); YOS uses `@YOperatingSystem_BOT`. Never share a token.

**Why:** Telegram's getUpdates API allows only one poller per token. Sharing a token causes 409 Conflict errors and unpredictable message routing.

**How to apply:** Every independent project with a Telegram integration must create its own bot via @BotFather. Document ownership in `memory/user_context.md`.

---

## D-010 — tools/ as the official execution layer (AOS alignment)

**Decision:** Create `tools/` as a structured execution layer with explicit, deterministic wrappers. Existing `utils/` and `store/` code is preserved and re-exported through `tools/`.

**Why:** CLAUDE.md prescribes: `tools/` = deterministic execution layer. This makes the execution layer explicit and inspectable. Agents call tools, not raw utils functions directly.

**How to apply:** New execution capabilities go in `tools/`. Utils/ and store/ remain as implementation detail. Agents import from `tools/`.
