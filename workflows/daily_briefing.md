# Workflow: Daily Intelligence Briefing

## Objective
Run all intelligence agents, compose a structured briefing, save it, and send it to Telegram by 07:00 IST daily.

## Inputs
- Live RSS feeds (HN, Yahoo Finance, BBC, Reuters)
- GmailOrg SQLite DB (must-reads, charges, renewals) — optional
- Health log gap detection from YOS DB

## Outputs
- Saved briefing row in `briefings` table
- Telegram message to `TELEGRAM_CHAT_ID`
- `agent_runs` rows for tech_intel, biz_intel, geo_intel

## Tools Used
- `agents/tech_intel.py` — HN + AI RSS feeds → 6 bullets
- `agents/biz_intel.py` — Yahoo Finance + startup RSS → 5 insights
- `agents/geo_intel.py` — BBC World + Reuters → 4 bullets
- `integrations/gmail.py` — must-reads + recent charges (read-only)
- `store/database.py:save_briefing()`, `days_since_health_log()`
- `utils/telegram.py:send_message()`

## Steps

1. **Run agents in sequence** (or parallel if independent)
   - `tech_intel.run()` → saves to agent_runs, returns summary
   - `biz_intel.run()` → saves to agent_runs, returns summary
   - `geo_intel.run()` → saves to agent_runs, returns summary

2. **Fetch Gmail snippet**
   - `integrations.gmail.get_gmail_snippet()` — degrades gracefully if DB not found

3. **Check health gap**
   - `store.database.days_since_health_log()` → if > 1, add reminder

4. **Compose briefing**
   - Merge all parts with section headers
   - Prepend date header

5. **Save and send**
   - `save_briefing(date, content)` — upsert to briefings table
   - `send_message(content)` — Telegram push

## Edge Cases
- If an agent fails: log error, skip section, continue composing
- If GmailOrg DB missing: skip inbox section entirely
- If Telegram send fails: briefing is still saved; /brief command can retrieve it later
- If briefing already exists for today: re-send without re-running agents

## Quality Bar
- All 3 agent summaries present and non-empty
- Sent to Telegram before 07:10 IST (10-minute tolerance)
- Briefing saved in DB regardless of Telegram status

## Trigger
- `scheduler/daily.py` → APScheduler CronTrigger(hour=7, minute=0, timezone="Asia/Kolkata")
- Manual: `python3 -m scheduler.main --now`
