# Patterns — Reusable Intelligence

Proven approaches that recur across the system. Reference before inventing.

---

## P-001 — Feed-based intel agent pattern

**When to use:** Any agent that reads RSS feeds, synthesizes with Claude, and saves the result.

**Structure:**
```python
def run() -> str:
    feeds = [feedparser.parse(url) for url in FEED_URLS]
    stories = []
    for feed in feeds:
        for e in feed.entries[:N]:
            stories.append(f"{e.get('title', '')} — {e.get('summary', '')[:200]}")
    prompt = f"<context>\n{chr(10).join(stories)}\n</context>\n\nSynthesize 5 bullets..."
    summary = claude.ask(prompt)
    save_agent_run(agent="tech_intel", summary=summary, raw_output="\n".join(stories))
    return summary
```

**Key decisions:**
- `feedparser` not httpx for all RSS ingestion
- Truncate each entry to ~200 chars before sending to Claude (cost control)
- Always save to `agent_runs` table for briefing composition + history
- Return the summary string for direct use in briefing.py

**Reference files:** `agents/tech_intel.py`, `agents/biz_intel.py`, `agents/geo_intel.py`

---

## P-002 — Claude tool-use loop pattern (deep research agent)

**When to use:** Any agent that needs multi-step reasoning with web search or DB access.

**Structure:**
```python
messages = [{"role": "user", "content": goal}]
for turn in range(max_turns):
    response = client.messages.create(model=model, tools=TOOL_DEFINITIONS, messages=messages)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason != "tool_use":
        break
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = execute_tool(block.name, block.input)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(result)})
    messages.append({"role": "user", "content": tool_results})
final_text = next(b.text for b in response.content if hasattr(b, "text"))
```

**Key decisions:**
- Use `claude-opus-4-6` for deep research agents (quality > cost)
- Use `claude-sonnet-4-6` for fast agents (cost-sensitive tasks)
- max_turns=15 prevents infinite loops
- Always save timing (`duration_ms`) to agent_runs

**Reference files:** `agents/claude/runner.py`, `agents/claude/tools.py`

---

## P-003 — Auth middleware pattern for Telegram bot

**When to use:** Every bot command handler. Prevents unauthorized access.

**Structure:**
```python
def _auth(func):
    async def wrapper(update, context):
        if str(update.effective_chat.id) != CHAT_ID:
            await update.message.reply_text("Unauthorized.")
            return
        return await func(update, context)
    return wrapper

@_auth
async def cmd_today(update, context):
    ...
```

**Key decisions:**
- Check against `TELEGRAM_CHAT_ID` env var (single-user system)
- Reject silently with "Unauthorized." — do not leak details
- Apply to every handler; never skip for "safe" commands

**Reference file:** `bot/dispatcher.py`

---

## P-004 — Briefing composition pattern

**When to use:** Daily briefing assembly from multiple agent outputs.

**Structure:**
```python
def compose_briefing() -> str:
    summaries = get_latest_agent_summaries(since_hours=24)
    gmail_snippet = get_gmail_snippet()  # read-only from GmailOrg DB
    health_alert = get_health_alert()
    
    parts = [f"🌅 *YOS Daily Briefing — {date}*\n"]
    for agent, summary in summaries.items():
        parts.append(f"*{agent.upper()}*\n{summary}\n")
    if gmail_snippet:
        parts.append(f"📬 *INBOX*\n{gmail_snippet}\n")
    if health_alert:
        parts.append(f"⚠️ *HEALTH*\n{health_alert}\n")
    
    content = "\n".join(parts)
    save_briefing(date=today, content=content)
    send_message(content)
    return content
```

**Key decisions:**
- Always cache briefing in `briefings` table before sending
- Degrade gracefully: if an agent fails, skip that section; don't abort briefing
- Use `get_latest_agent_summaries(since_hours=24)` not date-exact match (handles timezone drift)

**Reference file:** `intelligence/briefing.py`

---

## P-005 — PID file process management pattern

**When to use:** Any long-running process (bot, scheduler, web) that needs health monitoring and auto-restart.

**Structure:**
```python
# On startup (main.py)
import os
PID_FILE = "logs/bot.pid"
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

# In system_health.py
def is_running(pid_file: str) -> bool:
    if not os.path.exists(pid_file):
        return False
    pid = int(open(pid_file).read().strip())
    try:
        os.kill(pid, 0)  # signal 0 = existence check
        return True
    except ProcessLookupError:
        return False

def restart_if_dead(pid_file: str, cmd: list[str]):
    if not is_running(pid_file):
        subprocess.Popen(cmd, ...)
```

**Reference files:** `bot/main.py`, `scheduler/main.py`, `agents/claude/system_health.py`

---

## P-006 — GmailOrg read-only integration pattern

**When to use:** Any module in YOS that needs email data (briefing, spend summary, renewals).

**Structure:**
```python
import sqlite3, os

GMAIL_DB = os.getenv("GMAIL_ORG_DB_PATH", "../GmailOrganization/learning/db/gmail_org.db")

def get_gmail_snippet() -> str:
    if not os.path.exists(GMAIL_DB):
        return ""
    conn = sqlite3.connect(GMAIL_DB)
    conn.row_factory = sqlite3.Row
    # Read-only queries only — never write
    rows = conn.execute("SELECT ...").fetchall()
    conn.close()
    return format_snippet(rows)
```

**Key decisions:**
- Always check `os.path.exists(GMAIL_DB)` — graceful degradation if GmailOrg not running
- Read-only SELECT only — never INSERT/UPDATE/DELETE into GmailOrg DB
- Never import GmailOrg Python modules — only raw SQLite access

**Reference file:** `integrations/gmail.py`

---

## P-007 — Claude client wrapper pattern (retry + model selection)

**When to use:** Every module that calls the Anthropic API.

**Structure:**
```python
DEFAULT_MODEL = "claude-sonnet-4-6"
DEEP_MODEL = "claude-opus-4-6"

def ask(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 1024) -> str:
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            time.sleep(2 ** attempt)
    raise RuntimeError("Claude API failed after 3 attempts")
```

**Key decisions:**
- `ask()` for simple one-shot calls (Sonnet)
- `ask_deep()` or runner.py for tool-use/multi-turn (Opus)
- Always retry on RateLimitError with exponential backoff
- Never hardcode model strings — use module-level constants

**Reference file:** `utils/claude_client.py`

---

## P-008 — Evaluation scoring pattern (AOS compounding loop)

**When to use:** After every meaningful agent run or system output.

**Dimensions:** Correctness (1-5), Efficiency (1-5), Reusability (1-5), Clarity (1-5)

**Structure:**
```python
def self_evaluate(output: str, goal: str, context: str) -> dict:
    prompt = f"""
    Goal: {goal}
    Output: {output}
    
    Score this output on each dimension (1-5):
    - Correctness: accurate, grounded, internally consistent?
    - Efficiency: minimal waste, reused existing knowledge?
    - Reusability: creates value beyond this task?
    - Clarity: understandable, structured, actionable?
    
    Return JSON: {{"correctness": N, "efficiency": N, "reusability": N, "clarity": N, "notes": "..."}}
    """
    result = claude.ask(prompt)
    return json.loads(result)
```

**Stored in:** `evaluations` table in `store/database.py`
