# Learnings — AOS Operational Memory

Mistakes fixed, failure modes avoided, non-obvious insights from every execution cycle.

---

## L-001 — Telegram bot conflict (duplicate token)

**What happened:** YOS and GmailOrganization both used the same Telegram bot token. When both bots polled simultaneously, Telegram raised a 409 Conflict error and one bot stopped receiving updates.

**Fix:** Created a second bot via @BotFather for YOS specifically (`@YOperatingSystem_BOT`). Each project must own an exclusive bot token.

**Prevent:** Never share bot tokens across projects. Document token ownership per project in user_context.md.

---

## L-002 — Python 3.9 f-string backslash limitation

**What happened:** `f"...{'\n' + text}"` raises `SyntaxError` in Python 3.9. Backslash expressions are illegal inside f-string curly braces in Python < 3.12.

**Fix:** Extract the expression to a variable before the f-string:
```python
url_line = f"\n  {j['url']}" if j.get("url") else ""
msg = f"...{url_line}"
```

**Prevent:** Any f-string with conditional or escaped content — pre-assign to a variable. Always add `from __future__ import annotations` at top of every module.

---

## L-003 — python-multipart missing for FastAPI forms

**What happened:** FastAPI `Form()` parameter raises `RuntimeError: No module named 'python_multipart'` even though `fastapi` is installed.

**Fix:** `pip3 install python-multipart` — add to `requirements.txt`.

**Prevent:** Always list `python-multipart` whenever FastAPI is in the stack.

---

## L-004 — RemoteTrigger plan limit (1 slot used by GmailOrg)

**What happened:** RemoteTrigger allows only 1 remote scheduled session per plan. GmailOrganization already used the slot; YOS scheduling attempt was blocked.

**Fix:** Use `CronCreate` (in-session, durable=true) for persistence, plus APScheduler inside the running process for permanent scheduling. Both projects self-schedule locally.

**Prevent:** Do not rely on RemoteTrigger for new projects. Prefer local APScheduler.

---

## L-005 — feedparser is preferred over raw httpx for RSS

**What happened:** First iteration used raw httpx + BeautifulSoup XML parsing for RSS feeds. feedparser handles all RSS/Atom variants including malformed feeds, dates, and encoding.

**Fix:** Replace manual XML parsing with `feedparser.parse(url)`. Access entries via `feed.entries`.

**Prevent:** Always use feedparser for RSS ingestion. Only fall back to httpx for non-RSS URLs.

---

## L-006 — SQLite WAL mode required for concurrent bot + scheduler access

**What happened:** Bot and scheduler both write to `db/yos.db`. Without WAL mode, write locks cause occasional `database is locked` errors.

**Fix:** `conn.execute("PRAGMA journal_mode=WAL")` on every connection. Already in `store/database.py:get_conn()`.

**Prevent:** Always set WAL mode on SQLite connections in any multi-process setup.

---

## L-007 — Dynamic imports needed to avoid circular dependencies in scheduler

**What happened:** `scheduler/daily.py` importing `from agents import tech_intel` at module level caused circular imports when agents imported store, which imported utils.

**Fix:** Move all agent imports inside the function body:
```python
def run_daily():
    from agents import tech_intel
    tech_intel.run()
```

**Prevent:** In scheduler modules, always use dynamic (function-level) imports for domain packages.

---

## L-008 — pip not available on macOS; use pip3

**What happened:** `pip install` fails on macOS with `command not found`. System Python uses `pip3`.

**Fix:** All install commands must use `pip3 install`. All scripts use `python3 -m`.

**Prevent:** Document `pip3` / `python3` in all setup instructions.

---

## L-009 — New Telegram bot requires /start before responding

**What happened:** After creating `@YOperatingSystem_BOT` and starting the bot process, it received no messages — not even commands. User sent commands; nothing arrived.

**Fix:** User must find the bot on Telegram and tap **Start** before the bot is allowed to receive messages from that chat. This is a Telegram privacy restriction for new bots.

**Prevent:** Always document in setup: "Send /start to the bot first before testing any commands."

---

## L-010 — Shell working directory resets between Bash calls

**What happened:** After running a command in `/Users/yash/ClaudeWorkspace/YOS`, the next Bash call was executed from `/Users/yash/ClaudeWorkspace/GmailOrganization`. Shell state does not persist across tool calls.

**Fix:** Always prefix Bash commands with the full path: `cd /Users/yash/ClaudeWorkspace/YOS && <command>`.

**Prevent:** Never assume CWD. Always specify full paths or `cd` inline.

---

## L-011 — Anthropic tool-use loop requires multi-turn with stop_reason check

**What happened:** First tool-use implementation sent one request and returned the result, ignoring `stop_reason: "tool_use"`. Claude's response was incomplete (mid-tool-call).

**Fix:** Implement a loop: send → check `stop_reason` → if `tool_use`, execute all tool blocks → append results to messages → send again → repeat until `stop_reason: "end_turn"` or max_turns.

**Prevent:** Always implement tool-use as a multi-turn loop. See `agents/claude/runner.py` for the reference implementation.

---

## L-013 — Telegram Markdown parse errors from email content

**What happened:** GmailOrg daily digest failed with `Can't parse entities: can't find end of the entity starting at byte offset 444`. Email subjects/senders containing `_` or `*` characters (e.g. sender names) broke Telegram's Markdown parser.

**Fix:** Wrap the Markdown send in a try/except and fall back to plain text by stripping `*`, `_`, `` ` `` before retrying:
```python
try:
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
except Exception:
    plain = message.replace("*", "").replace("_", "").replace("`", "")
    await bot.send_message(chat_id=chat_id, text=plain)
```

**Prevent:** Any Telegram message containing user-generated content (email subjects, sender names) must have a plain-text fallback. Never trust external content to be Markdown-safe.

---

## L-014 — launchd KeepAlive causes duplicate processes if old nohup instances exist

**What happened:** When launchd services were loaded while nohup processes from a previous session were still running, two bot instances polled the same Telegram token simultaneously → 409 Conflict.

**Fix:** Before loading launchd services, kill all existing instances: `pkill -f "bot.main"`, `pkill -f "scheduler.main"`. Then load launchd. Going forward, launchd is the only process manager — never start processes with nohup alongside launchd services.

**Prevent:** Add a pre-load kill step to any setup/restart procedure. Document that nohup must never be used alongside launchd for the same module.

---

## L-012 — APScheduler timezone must be explicit for IST

**What happened:** Scheduler fired at wrong local time when timezone was not specified. Default is UTC; IST is UTC+5:30.

**Fix:** Pass `timezone="Asia/Kolkata"` to `CronTrigger`.

**Prevent:** Always specify timezone explicitly. Never rely on system timezone for scheduled jobs.
