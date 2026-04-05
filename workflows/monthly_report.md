# Workflow: Monthly Intelligence Report

## Objective
On the 1st of each month, generate a comprehensive month-in-review report covering goals, ideas shipped, health trends, career signals, and AI/tech themes — sent to Telegram and saved for reference.

## Inputs
- All DB tables for the past 30 days
- `briefings` table (full month of daily briefs)
- `goals` table (completed and stalled)
- `journal` table (full month of notes)
- `health_logs` table (30-day trends)
- `job_listings` table (career signals)
- `agent_runs` table (30 days of intelligence)

## Outputs
- Telegram message (multi-part if > 4000 chars)
- Saved `agent_runs` row for `monthly_reporter`
- Optional: updated `resume_versions` if skills detected

## Tools Used
- `agents/claude/monthly_reporter.py` — deep Opus agent
- `agents/claude/runner.py`
- `agents/claude/tools.py` — query_yos_db, send_telegram

## Steps

1. **Pull 30-day snapshot**
   - Goals: completed, active, stalled
   - Journal: count by category, notable entries
   - Health: average sleep, energy, stress over month
   - Ideas: shipped vs inbox
   - Career: new job matches, skills added
   - Intelligence: recurring themes across briefs

2. **Run monthly reporter agent** (claude-opus-4-6)
   - Goal: "Generate the monthly OS report. What did I accomplish? What patterns emerged? What should I carry forward? What should I drop?"
   - Must cover: goals recap, health summary, top ideas/decisions, career signals, AI/tech themes

3. **Send report**
   - Split at 4000 chars if needed (Telegram message limit)
   - Send via send_telegram
   - Save to `agent_runs` as `monthly_reporter`

## Quality Bar
- References actual data from the month (not hallucinated)
- Covers all 5 domains (goals, health, ideas, career, intel)
- Actionable "carry forward" recommendations included

## Trigger
- `scheduler/monthly.py` → APScheduler CronTrigger(day=1, hour=9, minute=0)
- Manual: `python3 -m scheduler.main --monthly`
